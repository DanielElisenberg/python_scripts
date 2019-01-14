import sys
import re
import argparse


def repl(m):
    return 'x' * len(m.group())


def mute_expression(text, expr, is_multiline):
    """ Mutes a given expression

    When trying to highlight keywords such as 'if' we 
    do not want it to affect strings or comments.
    This function finds all matches for the given
    expression and 'mutes' them by turning the matches
    into an equal amount of x's. This keeps the integrity
    of the indices of the text, while avoiding wrongful
    colorization within the bounds of the expression.

    Arguments:
    text          (string): the text to be colored
    expr           (regex): the expression to be muted
    is_multiline (boolean): if expression is multiline
    Returns:
    text (string):
    text          (string): text with muted expression
    expr_start      (list): starting indices
    expr_end        (list): ending indices 
    expr_match      (list): matches
    """
    if is_multiline:
        pattern = re.compile('{}'.format(expr), re.DOTALL)
    else:
        pattern = re.compile('{}'.format(expr))
    expr_start = []
    expr_end = []
    expr_match = []
    for match in pattern.finditer(text):
        expr_start.append(match.start())
        expr_end.append(match.end())
        expr_match.append(match.group())
    text = re.sub(pattern, repl, text)
    return text, expr_start, expr_end, expr_match


def unmute_expression(text, expr_start, expr_end, expr_match):
    """Unmutes an expression from indices and matches

    Unmutes a previously muted expression reinserting the
    found matches at the correct location in the text.

    Arguments:
    text      (string): text with muted expressions
    expr_start  (list): starting indices
    expr_end    (list): ending indices
    expr_match  (list): matches
    Returns:
    text      (string): text with unmutes expression 
    """
    for i in range(len(expr_match)):
        text = text[0:expr_start[i]] + \
            expr_match[i] + text[expr_end[i]:len(text)]
    return text


def colorize(text, regex, color, kind, strexpr, comexpr, mlcomexpr):
    """Highlights the text on matching expressions

    Goes through the text line by line and colors it 
    appropriately. It also makes sure to mute the comments,
    multilinecomments, and strings as these can contain other
    expressions that we do not wish to be colored within these
    bounds.

    Arguments:
    text     (string): text to be colored
    regex    (string): a regular expression
    color    (string): color to highlight matches
    kind     (string): what kind of syntax to match
    strexpr  (string): expression for strings
    comexpr  (string): expressions for comments
    mlcomexpr(string): expression for ml comments
    Returns:
    text     (string): the colored text
    """
    # mute strings and comments if necessary
    if(kind != "mlcomment"):
        text, mlcs, mlce, mlcm = mute_expression(text, mlcomexpr, True)
    if(kind != "string" and kind != "mlcomment"):
        text, ss, se, sm = mute_expression(text, strexpr, False)
    if(kind != "comment"):
        text, cs, ce, cm = mute_expression(text, comexpr, False)
    # find color locations with regex
    colorstart = []
    colorend = []
    colorstring = []
    if(kind == "mlcomment"):
        regex = re.compile('{}'.format(regex), re.DOTALL)
    else:
        regex = re.compile('{}'.format(regex))
    for match in regex.finditer(text):
        colorstart.append(match.start())
        colorend.append(match.end())
        colorstring.append(match.group())

    # unmute strings and comments if necessary
    if(kind != "string" and kind != "mlcomment"):
        text = unmute_expression(text, ss, se, sm)
    if(kind != "comment"):
        text = unmute_expression(text, cs, ce, cm)
    if(kind != "mlcomment"):
        text = unmute_expression(text, mlcs, mlce, mlcm)
    # color text based on locations and strings found by regex
    nudge = 0
    for i in range(len(colorstring)):
        highlightedexpr = "\033[{}m".format(
            color[0]) + colorstring[i] + "\033[0m"
        text = text[0:colorstart[i]+nudge] + \
            highlightedexpr + text[colorend[i]+nudge:len(text)]
        nudge += len("\033[{}m".format(color[0])) + len("\033[0m")
    return text


def colorfile(themefile, syntaxfile, sourcecode):
    """ Print sourcecode with color theme
        Connects the information in the theme and
        syntax files, and use the resulting dictionary
        to color the appropriate parts of the code.

        Arguments:
        themefile  (string): *.theme filename
        syntaxfile (string): *.syntax filename
        sourcecode (string): code to be printed
    """
    # Theme {type, color}
    theme_dict = {}
    # Syntax {regex, color}
    syntax_dict = {}
    # Text with highlighting
    highlighted = []

    with open(themefile) as tf:
        theme = tf.readlines()
    with open(syntaxfile) as sf:
        syntax = sf.readlines()
    with open(sourcecode) as sc:
        source = sc.readlines()
    text = ""
    for line in source:
        text += line
    # Build type: color dictionary
    for line in theme:
        line = line.replace(":", "")
        line = line.replace("\n", "")
        line = line.split(" ")
        theme_dict[line[0]] = line[1:]
    # Build type: color and regex dictionary
    for line in syntax:
        line = line.replace(" ", "")
        line = line.replace("\n", "")
        line = line.split("\":")
        theme_dict[line[1]].append(line[0])
        syntax_dict[line[1]] = theme_dict[line[1]]
    # Search and add color-codes to text
    strexpr = syntax_dict["string"][len(syntax_dict["string"])-1]
    comexpr = syntax_dict["comment"][len(syntax_dict["comment"])-1]
    mlcomexpr = syntax_dict["mlcomment"][len(syntax_dict["mlcomment"])-1]
    for key in syntax_dict:
        color_list = syntax_dict[key][:len(syntax_dict[key])-1]
        regex = syntax_dict[key][len(syntax_dict[key])-1]
        text = colorize(text, regex[1:], color_list,
                        key, strexpr[1:], comexpr[1:], mlcomexpr[1:])
    print(text)


if __name__ == '__main__':
    presets = {
        "pysyn": ["themes/pythemes/python.theme", "themes/pythemes/python.syntax", "demofiles/demo.py"],
        "pysyn2": ["themes/pythemes/python2.theme", "themes/pythemes/python2.syntax", "demofiles/demo.py"],
        "javasyn": ["themes/javathemes/java.theme", "themes/javathemes/java.syntax", "demofiles/demo.java"],
    }
    parser = argparse.ArgumentParser()
    # group = parser.add_mutually_exclusive_group()
    group1 = parser.add_argument_group("Preset")
    group1.add_argument("--preset", type=str, help="preset name for highlighting",
                        choices=["pysyn", "pysyn2", "javasyn"])
    group2 = parser.add_argument_group("Normal args")
    group2.add_argument("themefile", type=str,
                        help="*.theme filename", nargs='?')
    group2.add_argument("syntaxfile", type=str,
                        help="*.syntax filename", nargs='?')
    group2.add_argument("sourcefile", type=str,
                        help="sourcecode to be colored", nargs='?')

    args = parser.parse_args()
    if len(sys.argv) == 1 or (args.preset == '' and args.themefile == '' and args.syntaxfile == '' and args.sourcefile == ''):
        parser.print_help()
        exit(1)

    if args.preset:
        colorfile(*presets[args.preset])
    else:
        colorfile(args.themefile, args.syntaxfile, args.sourcefile)
