---
layout: home-page
---
# Het werkstuk
Dit profielwerkstuk behandelt een toepassing van wiskunde voor digitale apparaten: methodes om informatie zo te coderen dat er later eventuele fouten gecorrigeerd kunnen worden door wiskundige algoritmes. Het vakgebied van wiskundige error-correctie heet coderingstheorie. Deel één gaat over de coderingstheorie in het algemeen, en behandelt ook de Hamming-code. In het tweede deel wordt uitgelegd hoe coderingstheorie een toepassing heeft in QR-codes. Het hele proces van het maken van QR-codes wordt behandeld, inclusief de nodige wiskunde. Daarnaast laat ik zien hoe het bouwen van een QR-code geprogrammeerd kan worden.

[Download hier werkstuk](https://cdn.rawgit.com/TjeuKayim/qr-codes/431d9fe6/Werkstuk%20-%20Error-correctie%20van%20QR-codes.pdf)

# De Python code
```python
import numpy as np

class GF:
    def __init__(self, priem_poly):
        # Tabellen voor vermenigvuldigen:
        # Maak een lege tabel aan voor de exponenten van 2 in het Galoisveld (gf)
        self.exp = []
        # en een tabel voor de logaritmes (met 256 plaatsen)
        self.log = [0] * 256
        # Deze functie vult de tabel, waarbij als argument de priempolynnoom moet worden gegeven
        self.tabel_exponenten(priem_poly)

    def tabel_exponenten(self, priem_poly):
        x = 1
        # 2^i = x; i is element van [0,255>
        for i in range(0, 255):
            # voeg `x' (=2^i) toe aan de tabel voor exponenten
            self.exp.append(x)
            # en voeg `i' toe aan de tabel voor logaritmes
            self.log[x] = i
            # voor i+1 wordt x twee maal zo groot
            x = x * 2
            # is x groter dan 255, XOR x dan met de priempolynoom
            # (XOR wordt genoteerd als ^)
            if x > 255: x = x ^ priem_poly

    # Vermenigvuldigen in een Galoisveld kan nu met de rekenregel 2^a + 2^b = 2^(a+b)
    # Definiëer een functie om de argumenten x en y te vermenigvuldigen.
    def mul(self, x, y):
        # Vermenigvuldigen met 0 geeft 0
        if x == 0 or y == 0:
            return 0
        # modulo wordt geschreven als %
        return self.exp[(self.log[x] + self.log[y]) % 255]

    def poly_mul(self, p, q):
        """Polynomen vermenigvuldigen in een Galoisveld"""
        # r(x) = p(x) * q(x)
        # de lengte van r(x) is gelijk aan de som van de lengtes van p(x) en q(x) min 1
        r = [0] * (len(p) + len(q) - 1)
        # Voor elke term in p(x), ga alle termen in q(x) af
        for j in range(0, len(q)):
            for i in range(0, len(p)):
                # en tel het product van de te termen uit p(x) en q(x) op bij de term van r(x),
                # waarvan de exponent de som is van de exponenten in de vermenigvuldigde termen
                # Dit is zo'n voorbeeld waarbij code een stuk korter is dan de Nederlandse `uitleg'
                r[i + j] ^= self.mul(p[i], q[j])
        return r

    def poly_div(self, teller, noemer):
        '''Synthethic Division (Synthetische Deling)'''
        output = list(teller)
        # Voor alle diagonalen die passen
        for i in range(0, len(teller) - (len(noemer) - 1)):
            if output[i] != 0:  # log(0) bestaat niet
                # de eerste coöficiënt van de noemer wordt overgeslagen
                for j in range(1, len(noemer)):
                    if noemer[j] != 0:  # log(0) bestaat niet
                        # vermenigvuldig en tel op (XOR) bij het getal onderaan
                        output[i + j] ^= self.mul(noemer[j], output[i])
        # bepaal de positie van van het verticale streepje streepje
        # tussen het quotient en de tellen
        streepje = -(len(noemer) - 1)
        return output[:streepje], output[streepje:]


class Qr_code:
    '''QR Code generator'''
    # Initialiseer bewerkingen Galoisveld met de priempolynoom 285
    global gf
    gf = GF(285)

    def __init__(self, bericht, versie=1, mask=0, ec='H'):
        # Controleer of de arguments geldig zijn
        if versie not in range(1, 7):
            raise ValueError('Het versienummer moet tussen 1 en 6 liggen')
        if ec not in ('L', 'M', 'Q', 'H'):
            raise ValueError("De e.c-level moet L, M, Q of H zijn")
        if type(bericht) is not str:
            raise ValueError("Het bericht moet een 'string' zijn")
        if mask not in range(8):
            raise ValueError('mask moet tussen 1 en 7 liggen')
        while True:
            print('Genereer QR-code versie %i-%s' % (versie, ec))
            # Definiëer variables in huidige `Class'
            self.versie = versie
            self.v = versie - 1
            self.grootte = self.v * 4 + 21
            self.mask = mask
            self.ec = ec
            # Initialiseer een lege matrix met Numpy
            self.matrix = -np.ones((self.grootte, self.grootte), dtype=np.int)
            # Haal versie informatie op uit de tabel (two-demensional dictionary)
            info = __class__.versie_info[versie]
            total = info['total']
            msg_len = total - info[ec][0]
            aantal_blocks = info[ec][1]
            # codeer tekst naar bits met uft8
            try:
                self.blocks_bytes = self.encode_to_utf8(bericht, msg_len, aantal_blocks)
            except ValueError as err:
                # Is het bericht te lang:
                print(err)
                if self.versie == 6:
                    # is het versienummer 6, stop dan
                    return
                # vergroot het versienummer en probeer opnieuw of het past
                versie += 1
                continue
            # Als het bericht past, ga dan verder
            break
        ec = int(info[ec][0] / aantal_blocks)
        # codeer de blocks met de RS-code
        self.blocks_ec_bytes = [self.rs_encode(block, ec, True) for block in self.blocks_bytes]
        # combineer de data-bytes met de e.c.-bytes tot een string van bits
        qr_bits = self.interleave_blocks(rest=msg_len % aantal_blocks)
        self.voeg_finder_en_timing_patterns_toe()
        self.vul_qr_code(qr_bits)
        self.voeg_format_string_toe()

    # Versie info
    # total: totaal aantal bytes
    # (Aantal E.C-codewoorden, Aantal blocks)
    versie_info = {
        1: {
            'total': 26,
            'L': (7, 1),
            'M': (10, 1),
            'Q': (13, 1),
            'H': (17, 1),
        },
        2: {
            'total': 44,
            'L': (10, 1),
            'M': (16, 1),
            'Q': (22, 1),
            'H': (28, 1),
        },
        3: {
            'total': 70,
            'L': (15, 1),
            'M': (26, 1),
            'Q': (36, 2),
            'H': (44, 2),
        },
        4: {
            'total': 100,
            'L': (20, 1),
            'M': (36, 2),
            'Q': (52, 2),
            'H': (64, 4),
        },
        5: {
            'total': 134,
            'L': (26, 1),
            'M': (48, 2),
            'Q': (72, 4),  # andere blocks
            'H': (88, 4),
        },
        6: {
            'total': 172,
            'L': (36, 2),
            'M': (64, 4),
            'Q': (96, 4),
            'H': (112, 4),
        }
    }

    @staticmethod
    def encode_to_utf8(tekst, n, aantal_blocks):
        # zet tekst om in utf-8
        tekst = bytes(tekst, "utf8")
        # zet om naar bytes
        bits = ''.join(["{0:08b}".format(x) for x in tekst])
        # voeg de 'mode indicator' en het aantal tekens toe
        bits = '0100' + "{0:08b}".format(len(tekst)) + bits
        # voeg nullen toe totdat een veelvoud van 8 is bereikt
        # of de maximale lengte is bereikt
        while len(bits) % 8 and len(bits) != n * 8:
            bits += '0'
        # past het wel?
        if len(bits) > n * 8:
            raise ValueError('Het te coderen bericht is te groot voor de opgegeven versie')
        # herhaal 11101100 en 00010001 totdat de maximale lengte is bereikt
        i = 0
        while len(bits) != n * 8:
            if i % 2:
                bits += '00010001'
            else:
                bits += '11101100'
            i += 1
        # splits in bytes
        bytes_list = [int(bits[i:i + 8], 2) for i in range(0, len(bits), 8)]
        # deel lengte door het aantal blocks
        q = len(bytes_list) / aantal_blocks
        # rond qotiënt af naar beneden
        n = int(q)
        # is er een rest?
        rest = not q == n
        # splits data-bytes in meerdere blokken
        blocks = []
        x = 0
        for i in range(aantal_blocks):
            blocks.append(bytes_list[x:x + n])
            x += n
            # als er een rest is, tel halverwege 1 bij n op
            if (rest and i == 1): n += 1
        return blocks

    @classmethod
    def rs_encode(cls, msg_in, ec, return_only_ec_bytes=False):
        generator = cls.rs_generator_poly(ec)
        # Maak een berichtpolynoom met als laagste macht het aantal e.c.-codewoorden
        # en deel dit door de generatorpolynnoom
        quotient, rest = gf.poly_div(msg_in + [0] * ec, generator)
        # Return de codewoorden
        if return_only_ec_bytes:
            return rest
        else:
            return msg_in + rest

    # maak een generatorpolynoom voor een bepaald aantal error-correctie codewoorden
    @staticmethod
    def rs_generator_poly(n):
        # g(x)=1
        g = [1]
        # g(x)=1*(x-alpha^0)*(x-alpha^1) ... *(x-alpha^n-1)
        for i in range(0, n):
            g = gf.poly_mul(g, [1, gf.exp[i]])
        return g

    def interleave_blocks(self, rest):
        blocks = self.blocks_bytes
        ec_blocks = self.blocks_ec_bytes
        qr_bits = ''
        # loop alle kolommen af van de `message codewords' onder elkaar
        for i in range(len(blocks[0])):
            # voeg de `message codewords' toe
            for msg_bytes in blocks:
                qr_bits += "{0:08b}".format(msg_bytes[i])
        # als de laatste rijen langer zijn (bij 5-Q en 5-H)
        if rest:
            for i in (2, 3):
                qr_bits += "{0:08b}".format(blocks[i][-1])
        # loop alle kolommen af van de error-correctie codewoorden onder elkaar
        for i in range(len(ec_blocks[0])):
            # voeg de e.c-codewoorden toe
            for ec_bytes in ec_blocks:
                qr_bits += "{0:08b}".format(ec_bytes[i])
        return qr_bits

    def voeg_finder_en_timing_patterns_toe(self):
        g = self.grootte
        # voeg 'finder patterns' toe
        self.matrix[0:9, 0:9] = 0
        self.matrix[0:9, g - 8:g] = 0
        self.matrix[g - 8:g, 0:9] = 0
        for pos in ((0, 0), (g - 7, 0), (0, g - 7)):
            self.matrix[pos[0]:pos[0] + 7, pos[1]:pos[1] + 7] = 1
            self.matrix[pos[0] + 1:pos[0] + 6, pos[1] + 1:pos[1] + 6] = 0
            self.matrix[pos[0] + 2:pos[0] + 5, pos[1] + 2:pos[1] + 5] = 1
        # `alignment pattern'
        if self.versie > 1:
            i = g - 7
            self.matrix[i - 2:i + 3, i - 2:i + 3] = 1
            self.matrix[i - 1:i + 2, i - 1:i + 2] = 0
            self.matrix[(i, i)] = 1
        # voeg `timing patterns' toe (stippellijntjes)
        for i in range(8, g - 8, 2):
            self.matrix[(i, 6)] = self.matrix[(6, i)] = 1
            self.matrix[(i + 1, 6)] = self.matrix[(6, i + 1)] = 0

    def vul_qr_code(self, qr_bits):
        '''vul de qr-code met bits'''
        # masking
        masking = {
            0: (lambda x, y: (x + y) % 2),
            1: (lambda x, y: y % 2),
            2: (lambda x, y: x % 3),
            3: (lambda x, y: (x + y) % 3),
            4: (lambda x, y: (y / 2 + x / 3) % 2),
            5: (lambda x, y: (x * y) % 2 + (x * y) % 3),
            6: (lambda x, y: ((x * y) % 2 + (x * y) % 3) % 2),
            7: (lambda x, y: ((x * y) % 3 + (x + y) % 2) % 2)
        }

        class vector(list):
            def __iadd__(self, other):
                return self.__class__([self[0] + other[0], self[1] + other[1]])

        g = self.grootte
        pos = vector([g - 1, g - 1])
        last_bit = len(qr_bits) - 1
        for i, bit in enumerate(qr_bits):
            # stel de mask-formule gelijk aan 0
            mask = int(masking[self.mask](pos[0], pos[1]) == 0)
            # verwissel een 1 met een 0 als de vergelijking waar is
            self.matrix[tuple(pos)] = str(mask ^ int(bit))
            # self.matrix[tuple(pos)] = bit
            if i == last_bit:
                break
            if tuple(pos) == (7, 9):
                pos += (-2, 0)
                continue
            while True:
                dir = 'up'
                if pos[0] < 6 and pos[0] % 4 < 2:
                    dir = 'down'
                if pos[0] > 6 and (pos[0] - 1) % 4 < 2:
                    dir = 'down'
                if (pos[0] % 2 and pos[0] < 6) or (not pos[0] % 2 and pos[0] > 6):
                    pos += (-1, 0)
                # einde van de kolom
                elif (dir == 'up' and pos[1] == 0) or (dir == 'down' and pos[1] == g - 1):
                    pos += (-1, 0)
                else:
                    pos += (1, (-1 if dir == 'up' else 1))
                if self.matrix[tuple(pos)] == -1:
                    # als de module leeg is, zoek dan niet verder
                    break
        # maak overige pixels wit
        for i in range(0, g):
            for j in range(0, g):
                if self.matrix[(i, j)] == -1:
                    self.matrix[(i, j)] = 0 if masking[self.mask](i, j) else 1

    def voeg_format_string_toe(self):
        # Error-Correction Level
        ec_indicator = {
            'L': '01',
            'M': '00',
            'Q': '11',
            'H': '10',
        }
        format_string = ec_indicator[self.ec] + "{0:03b}".format(self.mask)
        # Binaire Synthetische Deling
        teller = output = [int(x) for x in list(format_string)] + [0] * 10
        # noemer is generatorpolynoom:
        noemer = [1, 0, 1, 0, 0, 1, 1, 0, 1, 1, 1]
        # Voor alle diagonalen die passen
        for i in range(0, len(teller) - (len(noemer) - 1)):
            if output[i] != 0:  # log(0) bestaat niet
                # de eerste coöficiënt van de noemer wordt overgeslagen
                for j in range(1, len(noemer)):
                    if noemer[j] != 0:  # log(0) bestaat niet
                        output[i + j] ^= 1  # 1*1=1
        separator = -(len(noemer) - 1)
        rest = output[separator:]
        format_string = format_string + ''.join([str(x) for x in rest])
        # zet om naar een nummer voor de masking
        format_string = int(format_string, 2)
        # mask met Exclusive OR
        format_string ^= 21522
        # zet weer om naar bits
        format_string = "{0:015b}".format(format_string)
        s = self.grootte
        # posities rondom de `finder patterns'
        format_pos = {(8, 0): 0, (8, 1): 1, (8, 2): 2, (8, 3): 3, (8, 4): 4, (8, 5): 5, (8, 7): 6, (8, 8): 7, (7, 8): 8,
                      (5, 8): 9, (4, 8): 10, (3, 8): 11, (2, 8): 12, (1, 8): 13, (0, 8): 14, (s - 8, 8): 7,
                      (s - 7, 8): 6, (s - 6, 8): 5, (s - 5, 8): 4, (s - 4, 8): 3, (s - 3, 8): 2, (s - 2, 8): 1,
                      (s - 1, 8): 0, (8, s - 7): 8, (8, s - 6): 9, (8, s - 5): 10, (8, s - 4): 11, (8, s - 3): 12,
                      (8, s - 2): 13, (8, s - 1): 14, }
        for pos, i in format_pos.items():
            self.matrix[pos] = format_string[14 - i]
        # voeg `dark module' toe
        self.matrix[(8, s - 8)] = 1

    def to_png(self, filename='qr-code.png', size=10, border=4):
        import png
        qr_code = np.pad(self.matrix, border, mode='constant', constant_values=0)
        qr_code = np.repeat(np.repeat(qr_code, size, axis=0), size, axis=1)
        replace = {
            -1: 200,
            1: 0,
            0: 255
        }
        qr_code_list = [[replace[j] for j in i] for i in np.swapaxes(qr_code, 0, 1)]
        png.from_array(qr_code_list, 'L').save(filename)

    def to_svg(self, filename='qr-code.svg', border=4):
        """Based on the given number of border modules to add as padding, this returns a
        string whose contents represents an SVG XML file that depicts this QR Code symbol."""
        size = self.grootte
        if border < 0:
            raise ValueError("Border must be non-negative")
        parts = []
        for y in range(size):
            for x in range(size):
                if self.matrix[x, y] == 1:
                    parts.append("M{},{}h1v1h-1z".format(x + border, y + border))
        string = """<?xml version="1.0" encoding="UTF-8"?>
            <!DOCTYPE svg PUBLIC "-//W3C//DTD SVG 1.1//EN" "http://www.w3.org/Graphics/SVG/1.1/DTD/svg11.dtd">
            <svg xmlns="http://www.w3.org/2000/svg" version="1.1" viewBox="0 0 {0} {0}">
            <rect width="100%" height="100%" fill="#FFFFFF" stroke-width="0"/>
            <path d="{1}" fill="#000000" stroke-width="0"/>
            </svg>
            """.format(size + border * 2, " ".join(parts))
        return string
        # file = open(filename, 'w')
        # file.write(string)
        # file.close()
```
