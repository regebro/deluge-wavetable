import math
import struct
import wave

WAVE_LENGTH = 2048
STAGE_SIZE = 12  # How many wave forms per "stage"
STEP_SIZE = WAVE_LENGTH / (2 * STAGE_SIZE)
BITDEPTH = 16
MAXVAL = 2 ** (BITDEPTH - 1) - 1
MINVAL = -(2 ** (BITDEPTH - 1))


def makesine():
    """Makes a sine"""
    return [
        int(MAXVAL * math.sin(2 * x * math.pi / WAVE_LENGTH))
        for x in range(WAVE_LENGTH)
    ]


def maketriangle(peak=None, length=WAVE_LENGTH):
    """Peak is how many samples in it the peak of the triangle
    1/4th of the total length creates a triangle. 0 is a saw. Anywhere
    inbetween created a skewed triangle.
    I haven't tried what happens if you make peak more than 1/4th the total length.
    More that 1/2 will definitely make an error.
    """
    if peak is None:
        peak = length // 4
    peak = round(peak)

    full = MAXVAL - MINVAL
    up = [round(MAXVAL * x / peak) for x in range(peak)]
    downlength = length - 2 * peak
    down = [round((full * x / downlength) + MINVAL) for x in range(downlength, 0, -1)]
    finish = [round((MAXVAL * x / peak) + MINVAL) for x in range(peak)]
    return up + down + finish


def morph(wavea, waveb, step, steps):
    """Averages two waves with a weighting"""
    bmul = step / steps
    amul = 1 - bmul
    return [round(a * amul + b * bmul) for a, b in zip(wavea, waveb)]


def sawsquare(squarestart, squareend):
    """A saw that has flat bits.

    squarestart and squareend are how many samples should be flat.
    If they add upp to WAVE_LENGTH, then it's a squarewave. You can
    then change pulse widths by having different length of start and end.
    """
    squarestart = round(squarestart)
    squareend = round(squareend)
    values = [MAXVAL] * squarestart
    values.extend(maketriangle(0, WAVE_LENGTH - (squarestart + squareend)))
    values.extend([-MAXVAL] * squareend)
    return values


def supersaw(teeth, firstlenght, stheight):
    """Makes a supersaw.

    teeth is the number of teeth,
    firstlength is the length of the first tooth
    """
    stlength = (WAVE_LENGTH - firstlenght) / (teeth - 1)
    slope = (MAXVAL - MINVAL + (teeth - 1) * stheight) / WAVE_LENGTH

    values = [round(MAXVAL - x * slope) for x in range(firstlenght)]

    for r in range(1, teeth):
        pos = len(values)
        values.extend(
            [
                round(MAXVAL - x * slope + stheight * r)
                for x in range(pos, int(pos + stlength))
            ]
        )

    values.extend([MINVAL] * (WAVE_LENGTH - len(values)))
    return values


#####################
#
# Some unused code examples:
#
# Morph a sine into a triangle:
# (useless, because the deluge can morph between waves all by itself)
#
#     waves = []
#     for x in range(0, STAGE_SIZE):
#         waves.append(morph(sine, triangle, x, STAGE_SIZE))
#
# Make skewed triangles (halfway between triangle and saw)
#
#         maketriangle(WAVE_LENGTH//8)
#
# Make a series of saws that turn into squares, kinda like clipping them:
#
#     waves = []
#     for x in range(1, STAGE_SIZE+1):
#         square = x * STEP_SIZE
#         waves.append(sawsquare(square, square))
#
# Make pulsewaves:
# (useless, because the deluge can change the pulsewidth of any wave)
#
#     waves = []
#     for x in range(0, STAGE_SIZE):
#         square = (STAGE_SIZE-x)*WAVE_LENGTH/(2*STAGE_SIZE)
#         waves.append(sawsquare(square, WAVE_LENGTH-square))
#
#####################


def makewaves():
    waves = []

    sine = makesine()
    triangle = maketriangle()

    # Add a sine:
    waves.append(sine)

    # Add the triangle:
    waves.append(triangle)

    # Add a pure saw:
    waves.append(sawsquare(0, 0))

    # And a supersaw:
    waves.append(supersaw(2, WAVE_LENGTH // 2, 40000))

    # Add a halfway square/halfway saw:
    waves.append(sawsquare(WAVE_LENGTH // 4, WAVE_LENGTH // 4))

    # Add a pure square:
    waves.append(sawsquare(WAVE_LENGTH // 2, WAVE_LENGTH // 2))

    # And a triangle again, so we can morph from square to triangle:
    waves.append(triangle)

    print(f"Made {len(waves)} waves")
    return waves


def wavencode(waves):
    data = b""
    for wav in waves:
        for val in wav:
            val = max(min(val, MAXVAL), MINVAL)
            data += struct.pack("<h", val)
    return data


def main():
    waves = makewaves()
    values = wavencode(waves)
    frames = int(len(values) / 2)
    with wave.open("basics.wav", "wb") as outfile:
        outfile.setnchannels(1)
        outfile.setsampwidth(2)
        outfile.setframerate(44100)
        outfile.setnframes(frames)
        outfile.writeframes(values)

    print(f"Wrote {frames} samples")


if __name__ == "__main__":
    main()
