# nand2badapple
Port Bad Apple videa na hack računalo iz tečaja `nand2tetris`.
[Originalni video](https://www.nicovideo.jp/watch/sm8628149)

Završni projekt iz kolegija `Moderni Računalni Sustavi`.

## Što radi
Ova Phyton skripta parsira svaku bitmap sliku (384x256x1) u folderu `./badapple` i pretvara u assembly kod za hack računalo ili skriptu koja stavlja vrijednosti direktno u framebuffer.

## Kako radi

S obzirom da jedna assembly datoteka može sadržavati samo 32768 instrukcija, morao sam cijeli video napraviti u nekoliko assembly datoteka. Nand2tetris nudi opciju skriptiranja za evaluaciju rješenja koju sam iskoristio za učitavanje assembly datoteka redom. Svaka `.asm` datoteka sadržava što više frameova moguće.

Drugi način rada koristi mogućnost skriptiranja kako bi stavio pixel vrijednosti direktno u framebuffer.

## Kompresija
Ovaj program koristi jako jednostavnu inter-frame kompresiju, odnosno, umjesto da svaki put crta cijeli frame, on crta samo one dijelove koji su se promijenili.

Kako hack računalo koristi 16-bitne vrijenosti za crtanje po ekranu, samo gleda koji dijelovi ekrana su drugačiji i stavlja promijenjenu 16-bitnu vrijednost.

Jedna assembly datoteka u prosjeku ima 10 frameova.

## Usage
1. Ako si na Linuxu i imaš instaliran `7z`, pokreni `./extract.sh`.  
   Ako nisi, ručno raspakiraj `frames.zip` tako da struktura mape bude:
    ```
    badapple/out-####.bmp
    .gitignore
    code.py
    extract.sh
    frames.zip
    pack.sh
    readme.md
    srcFull.txt
    ```
2. Pokreni `code.py` sa jednim od ovih argumenata:

    Windows              | Linux           | Objašnjenje
    ---------------------|-----------------|------------
    `python code.py`     | `./code.py`     | Pravi assembly datoteke i main.tst skriptu
    `python code.py asm` | `./code.py asm` | Pravi samo assembly datoteke
    `python code.py tst` | `./code.py tst` | Pravi samo main.tst skriptu

3. Otvori CPU Emulator i pokreni `assembly/script.tst` ili `main.tst`

## Popis datoteka
### Prije pokretanja
Datoteka                 | Svrha
-------------------------|-----------------------------------------
`code.py`                | Glavni kod
`frames.zip`             | Zip datoteka sa bitmap frameovima rezolucije 384x256x1
`srcFull.txt`            | Popis svih frameova koji se nalaze u badapple folderu. Hardkodano, ali brže za pristupiti. TODO: Maknuti ovisnost o ovoj datoteci
`extract.sh` i `pack.sh` | Skripte za pakiranje i raspakiranje `frames.zip` datoteke.
`readme.md`              | Ovo što trenutno čitate

### Poslije pokretanja
Datoteka                 | Svrha
-------------------------|----------------------------------------
`main.tst`               | Skripta koja stavlja vrijednosti pixela direktno u framebuffer
`empty.asm`              | Assembly file sa beskonačnom petljom kojeg `main.tst` koristi
`assembly/out-####.asm`  | Mapa sa dovršenim assembly datotekama (100 MB)
`assembly/script.tst`    | Skripta koja redom učitava assembly datoteke
`badapple/out-####.bmp`  | Otpakirana `frames.zip` datoteka (80 MB)
`test.tst`               | Privremena datoteka, kasnije postane `assembly/script.tst`