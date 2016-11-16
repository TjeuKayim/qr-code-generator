import numpy as np
import png
class GF:
    def __init__ (self,priem_poly):
        # Tabellen voor vermenigvuldigen:
        # Maak een lege tabel aan voor de exponenten van 2 in het Galoisveld (gf)
        self.exp = []
        # en een tabel voor de logaritmes (met 256 plaatsen)
        self.log = [0] * 256
        # Deze functie vult de tabel, waarbij als argument de priempolynnoom moet worden gegeven
        self.tabel_exponenten(priem_poly)
    def tabel_exponenten(self,priem_poly):
        x = 1
        # 2^i = x; i is element van [0,255>
        for i in range(0,255):
            # voeg `x' (=2^i) toe aan de tabel voor exponenten
            self.exp.append(x)
            # en voeg `i' toe aan de tabel voor logaritmes
            self.log[x] = i
            # voor i+1 wordt x twee maal zo groot
            x = x*2
            # is x groter dan 255, XOR x dan met de priempolynoom
            # (XOR wordt genoteerd als ^)
            if x>255: x = x ^ priem_poly
    # Vermenigvuldigen in een Galoisveld kan nu met de rekenregel 2^a + 2^b = 2^(a+b)
    # Definiëer een functie om de argumenten x en y te vermenigvuldigen.
    def mul(self,x,y):
        # Vermenigvuldigen met 0 geeft 0
        if x==0 or y==0:
                return 0
        # modulo wordt geschreven als %
        return self.exp[(self.log[x]+self.log[y]) % 255]
    def poly_mul(self,p,q):
        '''Polynomen vermenigvuldigen in een Galoisveld'''
        # r(x) = p(x) * q(x)
        # de lengte van r(x) is gelijk aan de som van de lengtes van p(x) en q(x) min 1
        r = [0] * (len(p)+len(q)-1)
        # Voor elke term in p(x), ga alle termen in q(x) af
        for j in range(0, len(q)):
            for i in range(0, len(p)):
                # en tel het product van de te termen uit p(x) en q(x) op bij de term van r(x),
                # waarvan de exponent de som is van de exponenten in de vermenigvuldigde termen
                # Dit is zo'n voorbeeld waarbij code een stuk korter is dan de Nederlandse `uitleg'
                r[i+j] ^= gf.mul(p[i], q[j])
        return r
    def poly_div(self,teller, noemer):
        '''Synthethic Division (Synthetische Deling)'''
        output = list(teller)
        # Voor alle diagonalen die passen
        for i in range(0, len(teller) - (len(noemer)-1)):
            if output[i] != 0: # log(0) bestaat niet
                # de eerste coöficiënt van de noemer wordt overgeslagen
                for j in range(1, len(noemer)):
                    if noemer[j] != 0: # log(0) bestaat niet
                        # vermenigvuldig en tel op (XOR) bij het getal onderaan
                        output[i+j] ^= self.mul(noemer[j], output[i])
        # bepaal de positie van van het verticale streepje streepje
        # tussen het quotient en de tellen
        streepje = -(len(noemer)-1)
        return output[:streepje], output[streepje:]


class Qr_code:
    '''QR Code generator'''
    # Initialiseer bewerkingen Galoisveld met de priempolynoom 285
    global gf
    gf = GF(285)
    def __init__(self,bericht,versie,mask,ec='H'):
        # Controleer of de arguments geldig zijn
        if versie not in range(1,7):
            raise ValueError('Het versienummer moet tussen 1 en 6 liggen')
        if ec not in ('L','M','Q','H'):
            raise ValueError("De e.c-level moet L, M, Q of H zijn")
        if type(bericht) is not str:
            raise ValueError("Het bericht moet een 'string' zijn")
        if mask not in range(8):
            raise ValueError('mask moet tussen 1 en 7 liggen')

        # Definiëer variables in huidige `Class'
        self.versie = versie
        self.v = versie-1
        self.grootte = self.v*4+21
        self.mask = mask
        self.ec = ec
        # Initialiseer een lege matrix met Numpy
        self.matrix = -np.ones((self.grootte,self.grootte),dtype=np.int)
        # Haal versie informatie op uit de tabel (two-demensional dictionary)
        info = __class__.versie_info[versie]
        total = info['total']
        msg_len = total - info[ec][0]
        aantal_blocks = info[ec][1]
        ec = int(info[ec][0] / aantal_blocks)
        # codeer tekst naar bits met uft8
        self.blocks_bytes = self.encode_to_utf8(bericht,msg_len,aantal_blocks)
        # codeer de blocks met de RS-code
        self.blocks_ec_bytes = [self.rs_encode(block,ec,True) for block in blocks]
        # combineer de data-bytes met de e.c.-bytes tot een string van bits
        qr_bits = self.interleave_blocks(rest = msg_len % aantal_blocks)
        self.voeg_finder_en_timing_patterns_toe()
        self.vul_qr_code(qr_bits)
        self.voeg_format_string_toe()
    # Versie info
    # Totaal aantal bytes; Aantal E.C-codewoorden; Aantal blocks
    versie_info = {
        1 : {
            'total' : 26,
            'L' : (7,1),
            'M' : (10,1),
            'Q' : (13,1),
            'H' : (17,1),
        },
        2 : {
            'total' : 44,
            'L' : (10,1),
            'M' : (16,1),
            'Q' : (22,1),
            'H' : (28,1),
        },
        3 : {
            'total' : 70,
            'L' : (15,1),
            'M' : (26,1),
            'Q' : (36,2),
            'H' : (44,2),
        },
        4 : {
            'total' : 100,
            'L' : (20,1),
            'M' : (36,2),
            'Q' : (52,2),
            'H' : (64,4),
        },
        5 : {
            'total' : 134,
            'L' : (26,1),
            'M' : (48,2),
            'Q' : (72,4), # andere blocks
            'H' : (88,4),
        },
        6 : {
            'total' : 172,
            'L' : (36,2),
            'M' : (64,4),
            'Q' : (96,4),
            'H' : (112,4),
        }
    }
    @staticmethod
    def encode_to_utf8(tekst,n,aantal_blocks):
        # zet tekst om in utf-8
        tekst = bytes(tekst, "utf8")
        # zet om naar bytes
        bits = ''.join(["{0:08b}".format(x) for x in tekst])
        # voeg de 'mode indicator' en het aantal tekens toe
        bits = '0100' + "{0:08b}".format(len(tekst)) + bits
        # voeg nullen toe totdat een veelvoud van 8 is bereikt
        # of de maximale lengte is bereikt
        while len(bits) % 8 and len(bits) != n*8:
            bits += '0'
        # past het wel?
        if len(bits) > n*8:
            raise ValueError('Het te coderen bericht is te groot voor deze versie')
        # herhaal 11101100 en 00010001 totdat de maximale lengte is bereikt
        i = 0
        while len(bits) != n*8:
            if i%2: bits += '00010001'
            else: bits += '11101100'
            i += 1
        # splits in bytes
        bytes_list = [int(bits[i:i+8],2) for i in range(0, len(bits), 8)]
        # deel lengte door het aantal blocks
        q = len(bytes_list)/aantal_blocks
        # rond qotiënt af naar beneden
        n = int(q)
        # is er een rest?
        rest = not q == n
        # splits data-bytes in meerdere blokken
        blocks = []
        x = 0
        for i in range(aantal_blocks):
            blocks.append(bytes_list[x:x+n])
            x += n
            # als er een rest is, tel halverwege 1 bij n op
            if(rest and i==1): n += 1
        return blocks
    @classmethod
    def rs_encode(cls,msg_in,ec,return_only_ec_bytes=False):
        generator = cls.rs_generator_poly(ec)
        # Pad the message, then divide it by the irreducible generator polynomial
        _, rest = gf.poly_div(msg_in + [0] * (len(generator)-1), generator)
        # The remainder is our RS code! Just append it to our original message to get our full codeword (this represents a polynomial of max 256 terms)
        msg_out = msg_in + rest
        # Return the codewords
        if return_only_ec_bytes:
            return rest
        else:
            return msg_out
    # maak een generatorpolynoom voor een bepaald aantal error-correctie codewoorden
    @staticmethod
    def rs_generator_poly(n):
        # g(x)=1
        g = [1]
        # g(x)=1*(x-alpha^0)*(x-alpha^1) ... *(x-alpha^n-1)
        for i in range(0,n):
            g = gf.poly_mul(g, [1, gf.exp[i]])
        return g
    def interleave_blocks(rest):
        qr_bits = ''
        # loop alle kolommen af van de `message codewords' onder elkaar
        for i in range(len(blocks[0])):
            # voeg de `message codewords' toe
            for msg_bytes in self.blocks_bytes:
                qr_bits += "{0:08b}".format(msg_bytes[i])
        # als de laatste rijen langer zijn (bij 5-Q en 5-H)
        if rest:
            for i in (2,3):
                qr_bits += "{0:08b}".format(blocks[i][-1])
        # loop alle kolommen af van de error-correctie codewoorden onder elkaar
        for i in range(ec):
            # voeg de e.c-codewoorden toe
            for ec_bytes in self.blocks_ec_bytes:
                qr_bits += "{0:08b}".format(ec_bytes[i])
        return qr_bits
    def voeg_finder_en_timing_patterns_toe(self):
        g = self.grootte
        # voeg 'finder patterns' toe
        self.matrix[0:9,0:9] = 0
        self.matrix[0:9,g-8:g] = 0
        self.matrix[g-8:g,0:9] = 0
        for pos in ((0,0),(g-7,0),(0,g-7)):
            self.matrix[pos[0]:pos[0]+7,pos[1]:pos[1]+7] = 1
            self.matrix[pos[0]+1:pos[0]+6,pos[1]+1:pos[1]+6] = 0
            self.matrix[pos[0]+2:pos[0]+5,pos[1]+2:pos[1]+5] = 1
        # `small finder patterns'
        def sm_finder(i):
            ''' voeg `small finder pattern' toe '''
            self.matrix[i-2:i+3,i-2:i+3] = 1
            self.matrix[i-1:i+2,i-1:i+2] = 0
            self.matrix[(i,i)] = 1
        if self.versie>1:
            sm_finder(g-7)
        # voeg `timing patterns' toe (stippellijntjes)
        for i in range(8,g-8,2):
            self.matrix[(i,6)] = self.matrix[(6,i)] = 1
            self.matrix[(i+1,6)] = self.matrix[(6,i+1)] = 0
    def vul_qr_code(self,qr_bits):
        '''vul de qr-code met bits'''
        # masking
        masking = {
            0:(lambda x,y: (x+y)%2),
            1:(lambda x,y: y%2),
            2:(lambda x,y: x%3),
            3:(lambda x,y: (x+y)%3),
            4:(lambda x,y: (y/2 + x/3)%2),
            5:(lambda x,y: (x*y)%2+(x*y)%3),
            6:(lambda x,y: ((x*y) % 2 + (x*y) % 3) % 2),
            7:(lambda x,y: ((x*y) % 3 + (x+y) % 2) % 2)
            }
        g = self.grootte
        pos = np.array((g-1,g-1))
        last_bit = len(qr_bits)-1
        for i,bit in enumerate(qr_bits):
            #qr_code[post] = bit
            self.matrix[tuple(pos)] = bit if masking[self.mask](pos[0],pos[1]) else 1-int(bit)
            if i==last_bit:
                break
            if tuple(pos) == (7,9):
                pos += (-2,0)
                continue
            while True:
                dir = 'up'
                if pos[0] < 6 and pos[0] % 4 < 2:
                    dir = 'down'
                if pos[0] > 6 and (pos[0]-1) % 4 < 2:
                    dir = 'down'
                if (pos[0]%2 and pos[0]<6) or (not pos[0]%2 and pos[0]>6):
                    pos += (-1,0)
                    # <--
                # einde van de kolom
                elif (dir=='up' and pos[1]==0) or (dir=='down' and pos[1]==g-1):
                    pos += (-1,0)
                    # <--
                else:
                    pos += (1,(-1 if dir=='up' else 1))
                if self.matrix[tuple(pos)] == -1:
                    # als het vakje niet vrij is, zoek verder naar een leeg vakje
                    break
        # maak overige pixels wit
        for i in range(0,g):
            for j in range(0,g):
                if self.matrix[(i,j)] == -1:
                    self.matrix[(i,j)] = 0 if masking[self.mask](i,j) else 1
    def voeg_format_string_toe(self):
        # 'format string'
        #format_string = ['001011010001001','001001110111110','001110011100111','001100111010000','000011101100010','000001001010101','000110100001100','000100000111011']
        # Error-Correction Level
        ec_indicator = {
            'L' : 1,
            'M' : 0,
            'Q' : 3,
            'H' : 2,
        }
        format_string = "{0:02b}".format(ec_indicator[self.ec])+"{0:03b}".format(self.mask)
        # Binaire Synthetische Deling
        teller = output = [int(x) for x in list(format_string)] + [0]*10
        # noemer is generatorpolynoom:
        noemer = [1,0,1,0,0,1,1,0,1,1,1]
        # Voor alle diagonalen die passen
        for i in range(0, len(teller) - (len(noemer)-1)):
            if output[i] != 0: # log(0) bestaat niet
                # de eerste coöficiënt van de noemer wordt overgeslagen
                for j in range(1, len(noemer)):
                    if noemer[j] != 0: # log(0) bestaat niet
                        output[i+j] ^= 1 # 1*1=1
        separator = -(len(noemer)-1)
        rest = output[separator:]
        format_string = format_string + ''.join([str(x) for x in rest])
        # zet om naar een nummer voor de masking
        format_string = int(format_string,2)
        # mask met Exclusive OR
        format_string ^= 21522
        # zet weer om naar bits
        format_string = "{0:015b}".format(format_string)
        s = self.grootte
        # posities rondom de `finder patterns'
        format_pos = {(8,0):0,(8,1):1,(8,2):2,(8,3):3,(8,4):4,(8,5):5,(8,7):6,(8,8):7,(7,8):8,(5,8):9,(4,8):10,(3,8):11,(2,8):12,(1,8):13,(0,8):14,(s-8,8):7,(s-7,8):6,(s-6,8):5,(s-5,8):4,(s-4,8):3,(s-3,8):2,(s-2,8):1,(s-1,8):0,(8,s-7):8,(8,s-6):9,(8,s-5):10,(8,s-4):11,(8,s-3):12,(8,s-2):13,(8,s-1):14,}
        for pos,i in format_pos.items():
            self.matrix[pos] = format_string[14-i]
        # voeg `dark module' toe
        self.matrix[(8,s-8)] = 1
    def to_png(self,filename='qr-code.png',size=10,border=4):
        qr_code = np.pad(self.matrix,4,mode='constant', constant_values=0)
        qr_code = np.repeat(np.repeat(qr_code,size, axis=0), size, axis=1)
        replace = {
            -1: 200,
            1: 0,
            0: 255
            }
        qr_code_list = [[replace[j] for j in i] for i in np.swapaxes(qr_code,0,1)]
        png.from_array(qr_code_list, 'L').save(filename)
def test():
    for i in range(4,7):
        for ec in ('L','M','Q','H'):
            Qr_code('QR-generator met Python 3.5',i,0,ec).to_png('test/%i-%s.png' % (i,ec))

def print_sd(teller=[65, 4, 54, 246, 70, 87, 38, 150, 230, 119, 55, 70, 134, 86, 247, 38, 150, 80, 236, 0, 0, 0, 0, 0, 0, 0],noemer=[1, 127, 122, 154, 164, 11, 68, 117]):
    print(teller,noemer)
    w = len(teller)+len(noemer)-1
    h = len(noemer)+1
    print(w,h)
    matrix = [['' for j in range(w)] for i in range(h)]
    for i,val in enumerate(teller):
        matrix[0][len(noemer)-1+i] = str(val)
    for i,val in enumerate(noemer[1:]):
        matrix[h-2-i][i] = str(val)
    output = list(teller)
    # Voor alle diagonalen die passen
    for i in range(0, len(teller) - (len(noemer)-1)):
        if output[i] != 0: # log(0) bestaat niet
            # de eerste coöficiënt van de noemer wordt overgeslagen
            for j in range(1, len(noemer)):
                if noemer[j] != 0: # log(0) bestaat niet
                    # vermenigvuldig en tel op (XOR) bij het getal onderaan
                    matrix[len(noemer)-j][i+j+len(noemer)-1] = str(gf.mul(noemer[j], output[i]))
                    output[i+j] ^= gf.mul(noemer[j], output[i])
    for i,val in enumerate(output):
        matrix[h-1][len(noemer)-1+i] = str(val)
    # bepaal de positie van van het verticale streepje streepje
    # tussen het quotient en de tellen
    streepje = -(len(noemer)-1)
    #return output[:streepje], output[streepje:]
    matrix_tex = ['&'.join(row) for row in matrix]
    matrix_tex = '\\\\\n'.join(matrix_tex)
    matrix_tex = '\\begin{tabular}{%s|%s}\n' % ('r' * (len(noemer)-1), 'r' * len(teller)) + matrix_tex
    matrix_tex += '\n\\end{tabular}'
    print(matrix_tex)
