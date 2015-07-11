#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Revision history
# - June 2015, Jens Troeger: initial port from Processing to Python
#

#
# The Image class wraps Pillow (PIL, Python Imaging Library) functionality into
# a Processing inspired interface.
#

import PIL.Image, PIL.ImageDraw, PIL.ImageFont, PIL.ImageColor

class Image :
    """
    The Image class is a composition of different modules from the Python
    Imaging Library Pillow (a PIL fork). For more documentation on the modules
    refer to the documentation:

      http://pillow.readthedocs.org/reference/index.html

    Furthermore, instances of this class provide functions that resemble the
    original Processing functions and map them to Pillow functions. That makes
    porting the original Processing code easier.

    BUGBUG: It seems to me that Pillow is not the most accurate way of drawing,
            the text seems to wobble and arcs break out of their respective bounding
            box. No support for anti-aliasing either. Perhaps using PyCairo instead
            of Pillow would be a better idea: http://cairographics.org/pycairo/
    """

    def __init__(self, width, height) :
        """
        Constructor. Creates an Image instance which represents an image with
        the width x height dimension.
        """
        self.image = PIL.Image.new("RGB", (width, height))
        self.draw = PIL.ImageDraw.Draw(self.image)


    def triangle(self, x1, y1, x2, y2, x3, y3, color) :
        """
        See the Processing function triangle():
        https://processing.org/reference/triangle_.html
        """
        self.draw.polygon([x1, y1, x2, y2, x3, y3], fill=color)


    def rect(self, x, y, width, height, color) :
        """
        See the Processing function rect():
        https://processing.org/reference/rect_.html
        """
        self.draw.rectangle([x, y, x + width, y + height], fill=color)


    def ellipse(self, x, y, width, height, color) :
        """
        See the Processing function ellipse():
        https://processing.org/reference/ellipse_.html
        """
        self.draw.ellipse([x, y, x + width, y + height], fill=color)


    def arc(self, x, y, width, height, start, end, fill, thick=1, segments=100) :
        """
        This is different than the Processing function arc():
        https://processing.org/reference/arc_.html

        In fact, Pillow does not provide for drawing an arc in a different pen
        width. One solution would be to use the (outdated?) Aggdraw module that
        can be found here: http://effbot.org/zone/pythondoc-aggdraw.htm

        The implementation of this function was taken from a Stackoverflow
        discussion: http://stackoverflow.com/questions/7070912/creating-an-arc-with-a-given-thickness-using-pils-imagedraw#22081171
        """
        bbox = [x, y, x + width, y + height]
        # Radians.
        start *= math.pi / 180
        end *= math.pi / 180
        # Angle step.
        da = (end - start) / segments
        # Shift end points with half a segment angle.
        start -= da / 2
        end -= da / 2
        # Ellipsis radii.
        rx = (bbox[2] - bbox[0]) / 2
        ry = (bbox[3] - bbox[1]) / 2
        # Bounding box centre.
        cx = bbox[0] + rx
        cy = bbox[1] + ry
        # Segment length.
        l = (rx+ry) * da / 2.0

        for i in range(segments):
            # Angle centre.
            a = start + (i+0.5) * da
            # x,y centre.
            x = cx + math.cos(a) * rx
            y = cy + math.sin(a) * ry
            # Derivatives.
            dx = -math.sin(a) * rx / (rx+ry)
            dy = math.cos(a) * ry / (rx+ry)
            # Draw.
            self.draw.line([(x-dx*l,y-dy*l), (x+dx*l, y+dy*l)], fill=fill, width=thick)


    def text(self, text, x, y, width, height, color, font) :
        """
        See the Processing function text():
        https://processing.org/reference/text_.html
        """

        # Helper function: take a word longer than the bounding box's width and
        # chop of as many letters in the beginning as fit, followed by an ellipsis.
        def chop(word) :
            total_str = ""
            total_width, _ = font.getsize("...")
            for c in word :
                c_width, _ = font.getsize(c)
                if total_width + c_width > width :
                    return total_str + c + "..."
                total_str += c
                total_width += c_width
            assert not "Should not be here, else 'word' fit into the bounding box"

        # Width and height of a single space character.
        space_width, space_height = font.getsize(" ")
        # Initialize text cursor to the top/left of the bounding box.
        w_x, w_y = x, y
        # Draw the text word by word and check bounding box.
        for word in text.split(" ") :
            w_width, w_height = font.getsize(word)
            # Overflowing width, break to the next line with leading.
            if w_x + w_width > width :
                # Special case: first word exceeds total length of a line.
                if w_x == x :
                    word = chop(word)
                else :
                    w_x, w_y = x, w_y + w_height + (space_height * 0.1)
                    # New line is outside height of the bounding box, done.
                    if w_y + w_height > height :
                        break;
            # Draw the word and move on to the position of the next.
            self.draw.text([w_x, w_y], word, fill=color, font=font)
            w_x += space_width + w_width


    def save(self, filename, format) :
        """
        Save this Image instance to the given filename, and encode it based
        on the given extension. It's assumed that filename and extension match.
        """
        self.image.save(filename, format)


    @staticmethod
    def font(name, size) :
        """
        Return a Pillow font instance for the given Truetype font 'name' of
        the given size 'size'.
        """
        return PIL.ImageFont.truetype(name, size)


    @staticmethod
    def colorHSB(h, s, b) :
        """
        Given the H,S,B values for the HSB color mode, convert them into the
        H,S,L values for the HSL color mode and return a Pillow color instance.
        This conversion is necessary because Pillow does not understand HSB. For
        more details about this conversion see this explanation:
        http://codeitdown.com/hsl-hsb-hsv-color/
        """
        H, S, B = h, s/100, b/100
        L = 0.5 * B * (2 - S)
        S = (B * S) / (1 - abs(2 * L - 1))
        return PIL.ImageColor.getrgb("hsl({}, {}%, {}%)".format(H, int(100 * S), int(100 * L)))


    @staticmethod
    def colorRGB(r, g, b) :
        """
        Given the R,G,B values for the RGB color mode, return a Pillow color
        instance.
        """
        return PIL.ImageColor.getrgb("rgb({}, {}, {})".format(r, g, b))


#
# The draw() function creates an Image instance and draws the cover. Returns
# an Image instance which is a composition of different Pillow functionality.
#

import argparse
import itertools
import json
import math
import os
import sys

def draw(title, subtitle, author, cover_width=400, cover_height=600) :
    """
    Main drawing function, which generates a cover of the given dimension and
    renders title, author, and graphics.
    """

    # Helper function that implements the Processing function map(). For more
    # details see
    # https://processing.org/reference/map_.html
    # http://stackoverflow.com/questions/17134839/how-does-the-map-function-in-processing-work
    def _map(value, istart, istop, ostart, ostop) :
        return ostart + (ostop - ostart) * ((value - istart) / (istop - istart))


    # Helper function to clip a given value based on a lower/upper bound.
    def _clip(value, lower, upper) :
        return lower if value < lower else upper if value > upper else value


    # Based on some initial constants and the title+author strings, generate a base
    # background color and a shape color to draw onto the background. Try to keep
    # these two colors somewhat compatible with each other by varying only their hue.
    def _processColors() :
        base_saturation = 100
        base_brightness = 90
        color_distance = 100
        invert = True

        counts = len(title) + len(author)
        # assert 2 <= counts <= 80
        color_seed = int(_map(counts, 2, 80, 10, 360))
        shape_color = Image.colorHSB(color_seed, base_saturation, base_brightness-(counts % 20))
        base_color = Image.colorHSB((color_seed + color_distance) % 360, base_saturation, base_brightness)
        if invert :
            shape_color, base_color = base_color, shape_color
        if 0 == counts % 10 :
            shape_color, base_color = base_color, shape_color
        return shape_color, base_color


    # Fill the background of the image with white.
    def _drawBackground() :
        fill = Image.colorRGB(255, 255, 255)
        cover_image.rect(0, 0, cover_width, cover_height, fill)


    # Draw the actual artwork for the cover. Given the length of the title string,
    # generate an appropriate sized grid and draw C64 PETSCII into each of the cells.
    # https://www.c64-wiki.com/index.php/PETSCII
    def _drawArtwork() :
        artwork_start_x = 0
        artwork_start_y = cover_height - cover_width

        grid_count, grid_total, grid_size = _breakGrid()
        cover_image.rect(0, 0, cover_width, cover_height * cover_margin / 100, base_color)
        cover_image.rect(0, 0 + artwork_start_y, cover_width, cover_width, base_color)
        c64_title = _c64Convert()
        for c, i in zip(itertools.cycle(c64_title), range(0, grid_total)) :
            grid_x = int(i % grid_count)
            grid_y = int(i / grid_count)
            x = grid_x * grid_size + artwork_start_x
            y = grid_y * grid_size + artwork_start_y
            _drawShape(c, x, y, grid_size)


    # Compute the graphics grid size based on the length of the book title.
    def _breakGrid() :
        min_title = 2
        max_title = 60
        length = _clip(len(title), min_title, max_title)

        grid_count = int(_map(length, min_title, max_title, 2, 11))
        grid_total = grid_count * grid_count
        grid_size = cover_width / grid_count
        return grid_count, grid_total, grid_size


    # Given the title of the book, filter through its characters and ensure
    # that only a certain range is used for the title; characters outside of
    # that range are replaced with a somewhat random character.
    def _c64Convert() :
        c64_letters = " qQwWeErRtTyYuUiIoOpPaAsSdDfFgGhHjJkKlL:zZxXcCvVbBnNmM1234567890."
        c64_title = ""
        for c in title :
            if c in c64_letters :
                c64_title += c
            else :
                c64_title += c64_letters[ ord(c) % len(c64_letters) ]
        return c64_title


    # Given an alphabetic character from the book's title string and the x, y
    # coordinates and size of the cell within the cover grid, draw a PETSCII
    # shape into that cell.
    def _drawShape(c, x, y, s) :
        shapeThickness = 10
        thick = int(s * shapeThickness / 100)
        if c in "qQ" :
            cover_image.ellipse(x, y, s, s, shape_color)
        elif c in "wW" :
            cover_image.ellipse(x, y, s, s, shape_color)
            cover_image.ellipse(x+thick, y+thick, s-(thick*2), s-(thick*2), base_color)
        elif c in "eE" :
            cover_image.rect(x, y+thick, s, thick, shape_color)
        elif c in "rR" :
            cover_image.rect(x, y+s-(thick*2), s, thick, shape_color)
        elif c in "tT" :
            cover_image.rect(x+thick, y, thick, s, shape_color)
        elif c in "yY" :
            cover_image.rect(x+s-(thick*2), y, thick, s, shape_color)
        elif c in "uU" :
            cover_image.arc(x, y, 2*s, 2*s, 180, 270, shape_color, thick)
        elif c in "iI" :
            cover_image.arc(x-s, y, 2*s, 2*s, 270, 360, shape_color, thick)
        elif c in "oO" :
            cover_image.rect(x, y, s, thick, shape_color)
            cover_image.rect(x, y, thick, s, shape_color)
        elif c in "pP" :
            cover_image.rect(x, y, s, thick, shape_color)
            cover_image.rect(x+s-thick, y, thick, s, shape_color)
        elif c in "aA" :
            cover_image.triangle(x, y+s, x+(s/2), y, x+s, y+s, shape_color)
        elif c in "sS" :
            cover_image.triangle(x, y, x+(s/2), y+s, x+s, y, shape_color)
        elif c in "dD" :
            cover_image.rect(x, y+(thick*2), s, thick, shape_color)
        elif c in "fF" :
            cover_image.rect(x, y+s-(thick*3), s, thick, shape_color)
        elif c in "gG" :
            cover_image.rect(x+(thick*2), y, thick, s, shape_color)
        elif c in "hH" :
            cover_image.rect(x+s-(thick*3), y, thick, s, shape_color)
        elif c in "jJ" :
            cover_image.arc(x, y-s, 2*s, 2*s, 90, 180, shape_color, thick)
        elif c in "kK" :
            cover_image.arc(x-s, y-s, 2*s, 2*s, 0, 90, shape_color, thick)
        elif c in "lL" :
            cover_image.rect(x, y, thick, s, shape_color)
            cover_image.rect(x, y+s-thick, s, thick, shape_color)
        elif c == ":" :
            cover_image.rect(x+s-thick, y, thick, s, shape_color)
            cover_image.rect(x, y+s-thick, s, thick, shape_color)
        elif c in "zZ" :
            cover_image.triangle(x, y+(s/2), x+(s/2), y, x+s, y+(s/2), shape_color)
            cover_image.triangle(x, y+(s/2), x+(s/2), y+s, x+s, y+(s/2), shape_color)
        elif c in "xX" :
            cover_image.ellipse(x+(s/2), y+(s/3), thick*2, thick*2, shape_color)
            cover_image.ellipse(x+(s/3), y+s-(s/3), thick*2, thick*2, shape_color)
            cover_image.ellipse(x+s-(s/3), y+s-(s/3), thick*2, thick*2, shape_color)
        elif c in "cC" :
            cover_image.rect(x, y + (thick * 3), s, thick, shape_color)
        elif c in "vV" :
            cover_image.rect(x, y, s, s, shape_color)
            cover_image.triangle(x+thick, y, x+(s/2), y+(s/2)-thick, x+s-thick, y, base_color)
            cover_image.triangle(x, y+thick, x+(s/2)-thick, y+(s/2), x, y+s-thick, base_color)
            cover_image.triangle(x+thick, y+s, x+(s/2), y+(s/2)+thick, x+s-thick, y+s, base_color)
            cover_image.triangle(x+s, y+thick, x+s, y+s-thick, x+(s/2)+thick, y+(s/2), base_color)
        elif c in "bB" :
            cover_image.rect(x+(thick*3), y, thick, s, shape_color)
        elif c in "nN" :
            cover_image.rect(x, y, s, s, shape_color)
            cover_image.triangle(x, y, x+s-thick, y, x, y+s-thick, base_color)
            cover_image.triangle(x+thick, y+s, x+s, y+s, x+s, y+thick, base_color)
        elif c in "mM" :
            cover_image.rect(x, y, s, s, shape_color)
            cover_image.triangle(x+thick, y, x+s, y, x+s, y+s-thick, base_color)
            cover_image.triangle(x, y+thick, x, y+s, x+s-thick, y + s, base_color)
        elif c == "0" :
            cover_image.rect(x+(s/2)-(thick/2), y+(s/2)-(thick/2), thick, s/2+thick/2, shape_color)
            cover_image.rect(x+(s/2)-(thick/2), y+(s/2)-(thick/2), s/2+thick/2, thick, shape_color)
        elif c == "1" :
            cover_image.rect(x, y+(s/2)-(thick/2), s, thick, shape_color)
            cover_image.rect(x+(s/2)-(thick/2), y, thick, s/2+thick/2, shape_color)
        elif c == "2" :
            cover_image.rect(x, y+(s/2)-(thick/2), s, thick, shape_color)
            cover_image.rect(x+(s/2)-(thick/2), y+(s/2)-(thick/2), thick, s/2+thick/2, shape_color)
        elif c == "3" :
            cover_image.rect(x, y+(s/2)-(thick/2), s/2+thick/2, thick, shape_color)
            cover_image.rect(x+(s/2)-(thick/2), y, thick, s, shape_color)
        elif c == "4" :
            cover_image.rect(x, y, thick*2, s, shape_color)
        elif c == "5" :
            cover_image.rect(x, y, thick*3, s, shape_color)
        elif c == "6" :
            cover_image.rect(x+s-(thick*3), y, thick*3, s, shape_color)
        elif c == "7" :
            cover_image.rect(x, y, s, thick*2, shape_color)
        elif c == "8" :
            cover_image.rect(x, y, s, thick*3, shape_color)
        elif c == "9" :
            cover_image.rect(x, y, thick, s, shape_color)
            cover_image.rect(x, y+s-(thick*3), s, thick*3, shape_color)
        elif c == "." :
            cover_image.rect(x+(s/2)-(thick/2), y+(s/2)-(thick/2), thick, s/2+thick/2, shape_color)
            cover_image.rect(x, y+(s/2)-(thick/2), s/2+thick/2, thick, shape_color)
        elif c == " " :
            cover_image.rect(x, y, s, s, base_color)
        else :
            assert not "Implement."


    # Allocate fonts for the title and the author, and draw the text.
    def _drawText() :
        fill = Image.colorRGB(50, 50, 50)

        title_font_size = int(cover_width * 0.08)
        title_font = Image.font("CooperHewitt-Bold", title_font_size)
        title_height = int((cover_height - cover_width - (cover_height * cover_margin / 100)) * 0.75)

        x = cover_height * cover_margin / 100
        y = cover_height * cover_margin / 100 * 2
        width = cover_width - (2 * cover_height * cover_margin / 100)
        height = title_height
        cover_image.text(title, x, y, width, height, fill, title_font)

        author_font_size = int(cover_width * 0.07)
        author_font = Image.font("CooperHewitt-Book", author_font_size)
        author_height = int((cover_height - cover_width - (cover_height * cover_margin / 100)) * 0.25)

        x = cover_height * cover_margin / 100
        y = title_height
        width = cover_width - (2 * cover_height * cover_margin / 100)
        height = author_height
        cover_image.text(author, x, y, width, height, fill, author_font)


    # Create the new cover image.
    cover_margin = 2
    cover_image = Image(cover_width, cover_height)

    # If any, append the book's subtitle to the title.
    if subtitle :
        title += ": " + subtitle

    # Draw the book cover.
    shape_color, base_color = _processColors()
    _drawBackground()
    _drawArtwork()
    _drawText()

    # Return the cover Image instance.
    return cover_image


#
# Run this as a stand-alone command-line tool as well.
#

if __name__ == "__main__" :
    """
    The main function allows to run the cover generation to run as a standalone
    command-line tool. Arguments can be passed, use -h or --help to get a list
    of available switches. The generated book cover is saved as an image file.
    """
    status = 0

    # Helper function to draw a cover and write it to a file. Python PIL supports
    # to write many more image formats, but we're restricting it to only three
    # (I'm too lazy to type more).
    def _draw_and_save(title, subtitle, author, filename) :
        cover_image = draw(title, subtitle, author)
        if filename == "-" :
            assert not "Implement."
        else :
            ext = os.path.splitext( os.path.basename( filename ) )[1][1:]
            if ext.upper() not in [ "JPEG", "PNG", "TIFF" ] :
                print("Unsupported image file format '" + ext + "', use JPEG, PNG, or TIFF")
                status = 1
            else :
                with open(filename, "wb") as f :
                    cover_image.save(f, ext)
        status = 0
        return status


    # Set up and parse the command line arguments passed to the program.
    usage = ""
    parser = argparse.ArgumentParser(usage=usage)

    parser.add_argument("-t", "--title", dest="title", help="Book title")
    parser.add_argument("-s", "--subtitle", dest="subtitle", help="Book subtitle", default="")
    parser.add_argument("-a", "--author", dest="author", help="Author(s) of the book")
    parser.add_argument("-o", "--cover", dest="outfile", help="Filename of the cover image")
    parser.add_argument("-j", "--json-covers", dest="json_covers", help="JSON file containing cover information")
    args = parser.parse_args()


    # A JSON file is given as command line parameter; ignore the other ones.
    # Read the file line by line and use the given information to generate the
    # book covers. The file contains lines of JSON maps of the format
    #
    #   {"authors": "..", "identifier": "..", "subtitle": null, "title": "..", "identifier_type": "Gutenberg ID", "filename": ".."}
    if args.json_covers :
        if os.path.isfile(args.json_covers) :
            with open(args.json_covers, "r") as f :
                try :
                    for line in f :
                        data = json.loads(line)
                        print("Generating cover for " + data["identifier"])
                        status = _draw_and_save(data["title"], data["subtitle"], data["authors"], data["filename"])
                except ValueError :
                    print("Error reading from JSON file, exiting")
                    status = 1
        else :
            print("JSON cover file does not exist: " + args.json_covers)
            status = 1


    # Generate only a single cover based on the given command line arguments.
    else :
        if not args.title or not args.author :
            print("Missing --title or --author argument, exiting")
            status = 1
        elif not args.outfile :
            print("No outfile specified, exiting")
            status = 1
        else :
            status = _draw_and_save(args.title, args.subtitle, args.author, args.outfile)


    # Terminate the program.
    sys.exit(status)
