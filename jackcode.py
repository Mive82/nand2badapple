#!/usr/bin/python3

import os

oldFrame = [[0 for i in range(1, 385)] for i in range(1, 257)]
currColor = True


def errorHandle(mes):
    print(mes)
    exit()


def invertData(data):
    temp = []
    for x in data:
        temp.append(255 - x)

    return temp


def initFrame(filename):

    # Otvara sliku kao binary file
    bmp = open(filename, 'rb')

    # U data čita podatke kao 8-bitne integere
    data = bytearray(bmp.read())

    # Pajtonovski kod koji cita duljinu bitmap headera u little-endian formatu
    offset = int(("".join(format(x, '02x') for x in reversed(data[10:14]))),
                 16)

    # Iscita je li prva boja u paleti crna ili bijela, pa poslije obrne
    # color1 = int(("".join(
    #    format(x, '02x') for x in reversed(data[offset - 8:offset - 4]))), 16)

    # Poslije headera se nalazi informacija o pikselima
    data = data[offset:]

    data = invertData(data)

    # Splita listu u dijelove po 48 bajta, odnosno 384 bitova, odnosno jedan redak na screenu
    # Slika ce biti omjera 3:2 jer je to najblize originalnom 4:3 omjeru
    # i lakse je za izracunati sredinu ekrana jer je 384 djeljivo sa 16
    chunks = [data[x:x + 48] for x in range(0, len(data), 48)]

    # Obrne redove jer su u bmp spremljeni naopako
    chunks.reverse()

    # Vrati ih nazad u data
    data = ""
    for i in chunks:
        for j in i:
            data += ("{:08b}".format(j))

    chunks = [data[x:x + 384] for x in range(0, len(data), 384)]

    return chunks


def frameToCoords(data):

    # Lista x coordinati
    startCoords = []
    endCoords = []
    startCoordsW = []
    endCoordsW = []

    global oldFrame

    # red = 0

    for x in data:
        i = 0
        tempStartCoordsBlack = []
        tempEndCoordsBlack = []

        tempStartCoordsWhite = []
        tempEndCoordsWhite = []

        black = False
        white = False
        for pixel in x:
            if pixel == '1':
                if not black:
                    black = True
                    tempStartCoordsBlack.append(i)
                if white:
                    white = False
                    tempEndCoordsWhite.append(i)
            elif pixel == '0':
                if black:
                    black = False
                    tempEndCoordsBlack.append(i)
                if not white:
                    white = True
                    tempStartCoordsWhite.append(i)
            else:
                errorHandle("Pixel Value not 0 or 1. In frameToCoords.")
            i += 1
        if black:
            tempEndCoordsBlack.append(i - 1)
            black = False
        if white:
            tempEndCoordsWhite.append(i - 1)
            white = False
        startCoords.append(tempStartCoordsBlack)
        startCoordsW.append(tempStartCoordsWhite)
        endCoords.append(tempEndCoordsBlack)
        endCoordsW.append(tempEndCoordsWhite)

    oldFrame = data

    return (startCoords, startCoordsW, endCoords, endCoordsW)


def switchColor():
    global currColor
    if currColor:
        kod = "do Screen.setColor (false);\n"
        currColor = False
    else:
        kod = "do Screen.setColor (true);\n"
        currColor = True
    return kod


def codeWriter(coords, outputFileName, outputFolder="."):

    global currColor
    output = open("{}/{}.jack".format(outputFolder, outputFileName), 'w')

    output.write("class " + outputFileName + " {\nfunction void draw() {\n")

    # kod = "class Main {\nfunction void main() {\n"
    # output.write(kod)

    startCoordsBlack = list(coords[0])
    startCoordsWhite = list(coords[1])
    endCoordsBlack = list(coords[2])
    endCoordsWhite = list(coords[3])

    # Ako je zadano crtanje bijelom bojom
    if not currColor:
        kod = switchColor()
        output.write(kod)

    i = 0
    for coord in startCoordsBlack:
        j = 0
        for k in coord:
            x = k
            y = endCoordsBlack[i][j]
            kod = "do Screen.drawLine({}, {}, {}, {});\n".format(
                x + 64, i, y + 64, i)
            output.write(kod)
            j += 1
        i += 1

    if len(startCoordsWhite) != 0:
        kod = switchColor()
        output.write(kod)
        i = 0
        for coord in startCoordsWhite:
            j = 0
            for k in coord:
                x = k
                y = endCoordsWhite[i][j]
                kod = "do Screen.drawLine({}, {}, {}, {});\n".format(
                    x + 64, i, y + 64, i)
                output.write(kod)
                j += 1
            i += 1

    kod = "return;\n}\n}\n"
    output.write(kod)
    output.close()


if __name__ == "__main__":

    # PLAN:
    # Napraviti kod koji ce na uzor crt monitora generirati jack kod za crtanje linija na ekranu jednu po jednu.
    # Naravno, to radim pod pretpostavkom da vm kod nema 32k limit, što vjerojatno ima. Bum vidil.
    # UPDATE:
    # VM ima limit od 32k VM naredbi... shit
    # Možda ako ima više fileova...
    # Nope...

    # Vraća polje linija na screnu

    inputFolder = "./badappleTest"
    outputFolder = "./jackOutput"
    filenames = os.listdir(inputFolder)

    frames = len(filenames)

    # filenames = open('srcPart.txt', 'r')

    currFrame = 1
    for i in filenames:
        i = inputFolder + "/" + os.path.splitext(i)[0] + ".bmp"
        data = initFrame(i)
        coords = frameToCoords(data)
        outputFileName = "frame{0:04d}".format(currFrame)
        currFrame += 1
        codeWriter(coords, outputFileName, outputFolder)

    jack = open("{}/Main.jack".format(outputFolder), 'w')
    jack.write("class Main {\nfunction void main() {\n")
    currFrame = 1
    for i in filenames:
        jack.write("do frame{0:04d}.draw();\n".format(currFrame))
        currFrame += 1
    jack.write("return;\n}\n}\n")
    jack.close()
