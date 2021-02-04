#!/usr/bin/env python3
import sys
import time
import shutil
import os

# Flag za debug output
debugFlag = False
# Cijeli framebuffer od zadnjeg framea
prevData = [0 for i in range(1, 10000)]
# Tehnikalija za delay loop
loopCodeNum = 0


# Pretvara dekadski broj u dvojni komplement
# Kod naden na stack-overflow
def twos_comp(val, bits):
    """compute the 2's complement of int value val"""
    if (val & (1 <<
               (bits - 1))) != 0:  # if sign bit is set e.g., 8bit: 128-255
        val = val - (1 << bits)  # compute negative value
    return val  # return positive value as is


# Obrne boje za prikaz
def invertData(data):
    temp = []
    for x in data:
        temp.append(255 - x)

    return temp


# Debug ispis u datoteku
def debugOutput(msg):
    if debugFlag:
        debug = open('debug.txt', 'a')
        debug.write(msg)
        debug.close()


# Parsira sliku i vraća array sa 16-bitnom reprezentacijom pikela
# (Da, napisao sam svoj vlastiti just-enough parser za bitmap, imam problema)
# Slika MORA biti 384x256x1 bitmap (bmp) BEZ color pallete informacije
def initData(filename):

    # Otvara sliku kao binary file
    bmp = open(filename + ".bmp", 'rb')

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

    # Inverta bitove jer po defaultu 1 je bijelo, a 0 je crno
    # Na hack racunalu je suprotno
    data = invertData(data)

    # Splita listu u dijelove po 48 bajta, odnosno 384 bitova, odnosno jedan redak na screenu
    # Slika ce biti omjera 3:2 jer je to najblize originalnom 4:3 omjeru
    # i lakse je za izracunati sredinu ekrana jer je 384 djeljivo sa 16
    chunks = [data[x:x + 48] for x in range(0, len(data), 48)]

    # Obrne redove jer su u bmp spremljeni naopako
    chunks.reverse()

    # Vrati ih nazad u data
    data = []
    for i in chunks:
        for j in i:
            data.append("{:08b}".format(j))

    # Upari svaka dva bajta, jer hack screen prima 16 bitova
    chunks = [data[x:x + 2] for x in range(0, len(data), 2)]

    # Spajanje i pretvaranje tih 2 bajta u dekadski broj
    data = []
    j = 0
    for i in chunks:
        temp = ''.join([str(j) for j in i])

        temp = temp[::-1]
        temp = twos_comp(int(temp, 2), 16)
        data.append(temp)

    return data


# Izracuna koliko linija bi zauzimao jedan I-frame
def computeIframe(data):
    lineCount = 0
    for i in data:
        if i == 0:
            continue
        elif i == 1 or i == -1:
            lineCount += 2
        elif i < -1:
            lineCount += 5
        else:
            lineCount += 4
    return lineCount


# Izracuna koliko linija bi zauzeo jedan P-frame s obzirom na zadnji frame
def computePframe(data):
    lineCount = 0
    global prevData
    screenCount = 0
    for i in data:
        if i != prevData[screenCount]:
            if i == 1 or i == 0 or i == -1:
                lineCount += 2
            elif i < -1:
                lineCount += 5
            else:
                lineCount += 4
        screenCount += 1
    return lineCount


# Vraca kod za crtanje I-framea
def outputIframe(data):
    ScreenCount = 0
    cursor = 16388
    kod = ""
    for i in data:
        if cursor > 24576:
            break
        if i == 0:
            kod += ""  # nema linija
        elif i == 1 or i == -1:
            kod += "@{}\nM={}\n".format(cursor, i)  # 2 linije
        # Za -32768 je edge case jer ga prvo moram stavit kao 32768 sto se promijeni u 32767 pa onda u -32767
        elif i < -1:
            t = i + 1
            t = -t
            kod += "@{}\nD=A\n@{}\nM=-D\nM=M-1\n".format(t, cursor)  # 5 linija
        else:
            kod += "@{}\nD=A\n@{}\nM=D\n".format(i, cursor)  # 4 linije

        # Postavljanje vrijednosti za racunanje iduceg P-framea
        prevData[ScreenCount] = i
        ScreenCount += 1
        cursor += 1
        # Prelazak u iduci red jer slika nije od ruba do ruba
        if ScreenCount % 24 == 0:
            cursor += 8

    return kod


# Vraca kod za crtanje P-framea
def outputPframe(data):
    ScreenCount = 0
    global prevData
    cursor = 16388
    kod = ""
    for i in data:
        if i != prevData[ScreenCount]:
            if i == 1 or i == 0 or i == -1:
                kod += "@{}\nM={}\n".format(cursor, i)  # 2 linije
            elif i < -1:
                t = i + 1
                t = -t
                kod += "@{}\nD=A\n@{}\nM=-D\nM=M-1\n".format(
                    t, cursor)  # 5 linija
            else:
                kod += "@{}\nD=A\n@{}\nM=D\n".format(i, cursor)  # 4 linije

            # Postavljanje vrijednosti za racunanje iduceg P-framea
            prevData[ScreenCount] = i
        ScreenCount += 1
        cursor += 1
        # Prelazak u iduci red jer slika nije od ruba do ruba
        if ScreenCount % 24 == 0:
            cursor += 8

    return kod


# Vraća kod za delay, koristen izmedu frameova
# Velicina je 18
def writeLoopKod(i=1):
    kod = ""
    global loopCodeNum
    while (i):
        kod += "@32767\nD=A\n@R0\nM=D\n(LOOP{})\n@R0\nM=M-1\nD=M\n@LOOP{}\nD;JGT\n".format(
            loopCodeNum, loopCodeNum)
        loopCodeNum += 1
        i -= 1
    return kod


# Pise framove u asm
def bmpToAsm(filenames, destFolder):

    # Koristena inter-frame kompresija na ideju I i P frameova
    # I frame ovdje čak nije ni puni frame, nego samo dijelovi koji nisu bijeli
    # P frame sadrzi samo informacije što se promijenilo od prošlog framea
    # Kompresija ovdje je oko 10:1, ondnosno u prosjeku jedan .asm file sadrzi 10 frameova

    totalFrames = len(filenames)
    tst = open('test.tst', 'w')
    i = 0

    while (i < totalFrames):
        x = directory + os.path.splitext(filenames[i])[0]
        data = initData(x)

        filename = "out-{0:04d}.asm".format(i)
        tst.write("load {};\n".format(filename))

        output = open("{}/{}".format(destFolder, filename), 'a')

        # 32767 - 4 cisto da ostane nesto na kraju
        capacityLeft = 32763

        # Pratim broj naredbi, da znam delay nastimati
        totalLines = computeIframe(data)

        # Pravljenje početnog I-framea
        capacityLeft = capacityLeft - totalLines - 18
        kod = outputIframe(data)
        output.write(kod)
        kod = writeLoopKod(1)
        output.write(kod)

        totalLines += 32768

        # Advance na iduci frame
        i += 1
        frames = 1
        if (i >= totalFrames):
            break
        x = directory + os.path.splitext(filenames[i])[0]
        data = initData(x)

        nextFrame = computePframe(data)

        # Puni ostatak filea sa P-frameovima
        while (capacityLeft - nextFrame - 18 > 0):

            capacityLeft = capacityLeft - nextFrame - 18
            totalLines += nextFrame
            kod = outputPframe(data)
            output.write(kod)
            kod = writeLoopKod(1)
            output.write(kod)
            totalLines += 32768
            i += 1
            frames += 1
            if (i >= totalFrames):
                break
            x = directory + os.path.splitext(filenames[i])[0]
            data = initData(x)
            nextFrame = computePframe(data)

        kod = "(END)\n@END\n0;JMP"
        output.writelines(kod)
        output.close()
        kod = "repeat {}".format(totalLines + 200000) + "{\nticktock;\n}\n"
        tst.write(kod)
    tst.close()
    os.rename("test.tst", "assembly/script.tst")


# Pise skriptu koja stavlja frameove direktno u framebuffer
def bmpToTst(filenames):

    # Ovdje je isto koristena inter-frame kompresija
    # Iako ovdje su koristeni samo P-frameovi

    output = open("empty.asm", 'w')
    output.write("@0\n0;JMP\n")
    output.close()

    output = open("main.tst", 'w')
    output.write("load empty.asm;\n")
    global prevData
    prevData = [0 for i in range(1, 10000)]

    for x in filenames:

        x = directory + os.path.splitext(x)[0]
        data = initData(x)

        ScreenCount = 0
        cursor = 16388

        for i in data:
            if i != prevData[ScreenCount]:
                # Ako je slika slucajno veca od 8k, samo prekini i idi na iduci frame
                if cursor > 24576:
                    break

                kod = "set RAM[{}] {};\n".format(cursor, i)
                output.writelines(kod)
                prevData[ScreenCount] = i
            ScreenCount += 1
            cursor += 1
            if ScreenCount % 24 == 0:
                cursor += 8

        # delay izmedu frameova
        kod = "repeat 100000 {\nticktock;\n}\n"
        output.write(kod)
    output.close()


if __name__ == "__main__":
    # Direktorij u kojem se nalaze frameovi u bitmap formatu
    directory = "./badapple/"
    if not (os.path.isdir(directory)):
        print("Direktorij {} ne postoji.".format(directory.split("./")[1]))
        exit()

    # Direktorij u koji ce se spremiti .asm fileovi
    assDirectory = "./assembly"
    # U fileu "srcFull.txt" se nalazi lista svih frameova 'ls > srcFull.txt'
    src = open('srcFull.txt', 'r')

    doAsm = False
    doTst = False

    argumenti = sys.argv

    # Parsiranje argumenata

    if len(argumenti) == 1:
        print("Radim sve.")
        doAsm = True
        doTst = True
    elif len(argumenti) == 2:
        if argumenti[1] != 'tst' and argumenti[1] != 'asm':
            print("Krivi argument na mjestu 1\nIzlazim.")
            exit()
        elif argumenti[1] == 'tst':
            doTst = True
            print("Radim samo 'main.tst' skriptu.")
        else:
            doAsm = True
            print("Radim samo .asm fileove.")
    else:
        print(
            "Previse argumenata.\nAko hoces da sve radim, nemoj nista proslijediti.\nIzlazim."
        )
        exit()

    if debugFlag:
        debugTxt = open('debug.txt', 'w')
        debugTxt.write("Begin Debug\n\n")
        debugTxt.close()

    filenames = []
    for i in src:
        filenames.append(i)
    if len(filenames) == 0:
        print(
            "Nije pronaden ni jedan frame, pogledaj jesu u listi 'srcFull.txt' dobro navedene datoteke.\nIzlazim."
        )
        exit()

    print("Pronadeno {} frameova.".format(len(filenames)))

    if doAsm:
        # Ako zavrsni direktorij postoji, obrisi ga cijelog i napravi novi
        if os.path.isdir(assDirectory):
            print("Mapa '{}' postoji, brišem ju.".format(
                assDirectory.split("./")[1]))
            shutil.rmtree(assDirectory)

        print("Pravim praznu mapu '{}'.".format(assDirectory.split("./")[1]))
        os.mkdir(assDirectory)

        print("Pišem asm fileove.")

        start = time.time()
        bmpToAsm(filenames, assDirectory)
        end = time.time()

        print("Pisanje .asm fileova dovrseno za {}s".format(int(end - start)))
        print(
            "Zavrsna skripta za ucitavanje svih .asm fileova se nalazi u mapi {}."
            .format(assDirectory.split("./")[1]))

    if doTst:
        print("Pišem 'main.tst' skriptu.")

        start = time.time()
        bmpToTst(filenames)
        end = time.time()

        print("Pisanje 'main.tst' skripte dovrseno za {}s".format(
            int(end - start)))
        print(
            "Zavrsna skripta za direktno pisanje u framebuffer 'main.tst' se nalazi pored ovog programa."
        )
