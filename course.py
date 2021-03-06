class CourseClass:
    """
    Class for a course from Super Mario Maker
    """
    def __init__(self):
        """
        Initializes the course with default settings
        """
        super().__init__()

        self.headerStruct = struct.Struct('>QI4xH6BQB7x66s2s4BHBBI96sII12xI')
        self.sprStruct = struct.Struct('>IIhbb4s4s4sbbhhbb')
        self.effectStruct = struct.Struct('>5bxxx')

    def load(self, data, progress=None):
        """
        Loads a Super Mario Maker course from bytes data.
        """

        header = self.headerStruct.unpack_from(data, 0)

        def parseStyle(raw):
            vals = [b'M1', b'M3', b'MW', b'WU']
            return vals.index(raw) if raw in vals else 0

        courseVer = header[0]; assert courseVer == 0xB
        # header[1] is the CRC32 hash; we don't need to load this
        self.creationYear = header[2]
        self.creationMonth = header[3]
        self.creationDay = header[4]
        self.creationHour = header[5]
        self.creationMinute = header[6]
        self.unk16 = header[7]
        self.unk17 = header[8]
        self.unk181F = header[9]
        self.unk20 = header[10]
        self.courseName = header[11].rstrip(b'\0').decode('utf-16be')
        self.style = parseStyle(header[12])
        self.unk6C = header[13]
        self.theme = header[14] % 6
        self.unk6E = header[15]
        self.unk6F = header[16]
        self.timeLimit = header[17]
        self.autoscroll = header[18]
        self.unk73 = header[19]
        self.unk7475 = header[20]
        self.unk76D7 = header[21] # this reeeeeally needs to be figured out ASAP
        self.unkD8DB = header[22]
        self.unkDCDF = header[23]
        numItems = header[24]


        effects = []
        for i in range(300):
            effinfo = self.effectStruct.unpack_from(data, 0x145F0 + 8 * i)
            eff = Effect(*effinfo)
            effects.append(eff)


        self.sprites = []
        for i in range(numItems):
            sprinfo = list(self.sprStruct.unpack_from(data, 0xF0 + 32 * i))

            # Replace the effect index with the Effect object itself
            eff = None if sprinfo[11] == -1 else effects[sprinfo[11] % 300]
            sprinfo[11] = eff

            # Fix up the positions
            sprinfo[0] = sprinfo[0] // 10 - 8
            sprinfo[1] = sprinfo[1] // 10
            sprinfo[2] = sprinfo[2] // 10 - 8

            spr = SpriteItem(*sprinfo)
            self.sprites.append(spr)

            spr.UpdateListItem()
            spr.UpdateDynamicSizing()


        # Success return value
        return True


    def save(self):
        """
        Save the course back to a file
        """
        header = self.headerStruct.pack(
            0x0B,
            0, # we can't calculate the hash yet; we fill it in later
            self.creationYear,
            self.creationMonth,
            self.creationDay,
            self.creationHour,
            self.creationMinute,
            self.unk16,
            self.unk17,
            self.unk181F,
            self.unk20,
            self.courseName.encode('utf-16be').ljust(66, b'\0'),
            [b'M1', b'M3', b'MW', b'WU'][self.style % 4],
            self.unk6C,
            self.theme,
            self.unk6E,
            self.unk6F,
            self.timeLimit,
            self.autoscroll,
            self.unk73,
            self.unk7475,
            self.unk76D7,
            self.unkD8DB,
            self.unkDCDF,
            len(self.sprites),
            )


        effects = []
        sprdata = b''
        for spr in self.sprites:

            if spr.effect is None:
                b = None
            else:
                b = self.effectStruct.pack(
                    spr.effect.unk00,
                    spr.effect.unk01,
                    spr.effect.unk02,
                    spr.effect.unk03,
                    spr.effect.unk04,
                    )

            if b is None:
                thisEffIdx = -1
            elif b in effects:
                thisEffIdx = effects.index(b)
            else:
                effects.append(b)
                thisEffIdx = len(effects) - 1

            sprdata += self.sprStruct.pack(
                spr.objx * 10 + 80,
                spr.objz * 10,
                spr.objy * 10 + 80,
                spr.width,
                spr.height,
                spr.spritedata[:4],
                spr.spritedata_sub,
                spr.spritedata[4:],
                spr.type,
                spr.type_sub,
                spr.linkingID,
                thisEffIdx,
                spr.costumeID,
                spr.costumeID_sub,
                )

        sprdata = sprdata.ljust(0x14500, b'\0')

        while len(effects) < 300: effects.append(DEFAULT_EFFECT)
        effdata = b''.join(effects)

        cdt = bytearray(header + sprdata + effdata + b'\0' * 0xB0)

        hash = binascii.crc32(cdt[16:]) & 0xFFFFFFFF
        # Shamelessly splice this into the cdt
        cdt[0x8] = hash >> 24
        cdt[0x9] = (hash >> 16) & 0xFF
        cdt[0xA] = (hash >> 8) & 0xFF
        cdt[0xB] = hash & 0xFF

        return bytes(cdt)


    # Python hax: automatically notify SLib whenever the style or theme changes!
    @property
    def style(self):
        return self._style
    @style.setter
    def style(self, value):
        SLib.Style = value
        self._style = value
    @property
    def theme(self):
        return self._theme
    @theme.setter
    def theme(self, value):
        SLib.Theme = value
        self._theme = value


    # The following insanely long constant was written by hand by RoadrunnerWMC.
    TERRAIN_EDGES = (24, 24, 28, 28, 24, 24, 28, 28, 25, 25, 34, 0, 25, 25, 34, 0, 27, 27, 33, 33, 27, 27, 1, 1, 6, 6, 36, 44, 6, 6, 45, 9, 24, 24, 28, 28, 24, 24, 28, 28, 25, 25, 34, 0, 25, 25, 34, 0, 27, 27, 33, 33, 27, 27, 1, 1, 6, 6, 36, 44, 6, 6, 45, 9, 30, 30, 29, 29, 30, 30, 29, 29, 32, 32, 38, 40, 32, 32, 38, 40, 31, 31, 37, 37, 31, 31, 41, 41, 35, 35, 39, 48, 49, 35, 49, 52, 30, 30, 29, 29, 30, 30, 29, 29, 4, 4, 42, 2, 4, 4, 42, 2, 31, 31, 37, 37, 31, 31, 41, 41, 46, 46, 50, 54, 46, 46, 57, 67, 24, 24, 28, 28, 24, 24, 28, 28, 25, 25, 34, 0, 25, 25, 34, 0, 27, 27, 33, 33, 27, 27, 1, 1, 6, 6, 36, 44, 6, 6, 45, 9, 24, 24, 28, 28, 24, 24, 28, 28, 25, 25, 34, 0, 25, 25, 34, 0, 27, 27, 33, 33, 27, 27, 1, 1, 6, 6, 36, 44, 6, 6, 45, 9, 30, 30, 29, 29, 30, 30, 29, 29, 32, 32, 38, 40, 32, 32, 38, 40, 5, 5, 43, 43, 5, 5, 3, 3, 47, 47, 51, 56, 47, 47, 55, 68, 30, 30, 29, 29, 30, 30, 29, 29, 4, 4, 42, 2, 4, 4, 42, 2, 5, 5, 43, 43, 5, 5, 3, 3, 15, 15, 53, 69, 15, 15, 70, 12)

    def regenerateGround(self, groundsprites):
        """
        Recalculate edge pieces for selected ground sprites (sprite 7)
        """
        # Make a list of all ground sprites in the level
        allGroundSprites = []
        for spr in self.sprites:
            if spr.type != 7: continue
            allGroundSprites.append(spr)

        for this in groundsprites:
            if not isinstance(this, SpriteItem): continue
            if this.type != 7: continue

            # Make a bitfield showing which edges are touching another
            # ground sprite:
            # 1 2 3
            # 4   5
            # 6 7 8
            edges = 0
            for other in allGroundSprites:

                xAlign, yAlign = 0, 0

                if this.objx - 16 <= other.objx < this.objx:
                    # To the left
                    xAlign = 1
                elif this.objx == other.objx:
                    # Horizontally-aligned
                    xAlign = 2
                elif this.objx < other.objx <= this.objx + 16:
                    # To the right
                    xAlign = 3

                if this.objy - 16 <= other.objy < this.objy:
                    # Below
                    yAlign = 3
                elif this.objy == other.objy:
                    # Vertically-aligned
                    yAlign = 2
                elif this.objy < other.objy <= this.objy + 16:
                    # Above
                    yAlign = 1

                # Depending on where the other tile is relative to this one,
                # OR-in a bit, flagging where it is
                if (xAlign, yAlign) == (1, 1): edges |= 128
                elif (xAlign, yAlign) == (2, 1): edges |= 64
                elif (xAlign, yAlign) == (3, 1): edges |= 32
                elif (xAlign, yAlign) == (1, 2): edges |= 16
                elif (xAlign, yAlign) == (3, 2): edges |= 8
                elif (xAlign, yAlign) == (1, 3): edges |= 4
                elif (xAlign, yAlign) == (2, 3): edges |= 2
                elif (xAlign, yAlign) == (3, 3): edges |= 1

            # Edges of the stage also count for ground edge-detection
            if this.objx <= SMM_X_MIN * 16:
                edges |= 0x94
            elif this.objx >= SMM_X_MAX * 16:
                edges |= 0x29
            if this.objy <= SMM_Y_MIN * 16:
                edges |= 0x07
            elif this.objy >= SMM_Y_MAX * 16:
                edges |= 0xE0

            # Splice the correct value into the sprite data
            this.spritedata = this.spritedata[:7] + bytes([self.TERRAIN_EDGES[edges]])

            # Update stuff
            this.UpdateDynamicSizing()
            this.UpdateListItem()


