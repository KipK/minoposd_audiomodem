#!/usr/bin/env python

from os import path as op
from optparse import OptionParser

# uavobjects to use
UAVOBJECTS_USE = ['flighttelemetrystats', 'gcstelemetrystats', 'attitudeactual',
                  'flightstatus', 'manualcontrolcommand', 'gpsposition',
                  'gpstime', 'gpsvelocity', 'systemalarms']

# enums to copy, must be in one of the uavobjects to use
ENUMS_USE = ['FlightStatusFlightModeOptions', 'SystemAlarmsAlarmElem']

# sizes in bytes
TYPE_SIZE = {'uint8_t': 1, 'int8_t': 1, 'uint16_t': 2, 'int16_t': 2,
             'uint32_t': 4, 'int32_t': 4, 'float': 4}

class UAVObject:
    def __init__(self, name, objid, fields):
        self.name = name
        self.objid = objid
        self.fields = fields
    def __repr__(self):
        return '%s id: %s fields: %s' % (self.name, self.objid, self.fields)


def parse_code(uavobject_names, enum_names, uavobject_dir):
    uavobjects = []
    enums = []
    for name in uavobject_names:
        fname = op.join(uavobject_dir, name + '.h')
        objid = None
        fields = []
        in_struct = False
        with open(fname, 'r') as fid:
            for line in fid.readlines():
                line = line.strip()
                if len(line) == 0:
                    continue
                if line.startswith('#define %s_OBJID' % name.upper()):
                    objid = line.split(' ')[-1]
                    continue
                if line.startswith('typedef struct'):
                    in_struct = True
                    struct_pos = 0
                    continue
                if in_struct and line.split(' ')[-1][:-1].lower() == name + 'data':
                    in_struct = False
                    continue
                if in_struct:
                    parts = line[:-1].split(' ')
                    field_size = TYPE_SIZE[parts[0]]
                    field_name = parts[-1]
                    if field_name.endswith(']'):
                        pos = field_name.find('[')
                        n_elems = int(field_name[pos + 1:-1])
                        field_name = field_name[:pos]
                    else:
                        n_elems = 1
                    fields.append((field_name, struct_pos))
                    struct_pos += n_elems * field_size

                for enum in enum_names:
                    if line.startswith('typedef enum') and line.endswith(enum + ';'):
                        line = line.replace('{', '{\n')
                        line = line.replace(',', ',\n')
                        line = line.replace('}', '\n}')
                        enums.append(line)

            if objid is None:
                print 'warning: object %s not found' % name
                continue
            # add an extra field with the lenght
            fields.append(('len', struct_pos))
            uavobjects.append(UAVObject(name, objid, fields))
        fid.close()

    return uavobjects, enums


if __name__ == '__main__':

    from optparse import OptionParser

    parser = OptionParser()
    parser.add_option('-i', '--in', dest='infile',
                    help='input file (default UAVTalk.h)', default=None)
    parser.add_option('-o', '--out', dest='outfile',
                    help='output file (default UAVTalk.h)', default=None)
    parser.add_option('-d', "--dir", dest='dir',
                    help='Openpilot directory')

    (opts, args) = parser.parse_args()

    uavobject_dir = op.join(opts.dir, 'build', 'uavobject-synthetics', 'flight')
    if not op.exists(uavobject_dir):
        raise ValueError('Directory %s does not exists, build OP code first'
                         % uavobject_dir)

    fname_in = opts.infile if opts.infile is not None else 'UAVTalk.h'
    fname_out = opts.outfile if opts.outfile is not None else 'UAVTalk.h'

    # read the input file
    with open(fname_in, 'r') as fid:
        lines_in = fid.readlines()
    fid.close()

    write_line = True
    with open(fname_out, 'w') as fid:
        for line in lines_in:
            if line.startswith('#if defined VERSION_UNRELEASED_NEXT'):
                fid.write(line)
                write_line = False

                # insert new code
                fid.write('// Code generated using uavtalk_update.py, do not edit!\n\n')

                uavobjects, enums = parse_code(UAVOBJECTS_USE, ENUMS_USE, uavobject_dir)
                for obj in uavobjects:
                    print obj
                    this_line = '#define %s_OBJID' % obj.name.upper()
                    this_line += ' ' * (55 - len(this_line))
                    this_line += obj.objid + '\n'
                    fid.write(this_line)

                fid.write('\n\n')
                for obj in uavobjects:
                    for field in obj.fields:
                        this_line = '#define %s_OBJ_%s' % (obj.name.upper(), field[0].upper())
                        this_line += ' ' * (55 - len(this_line))
                        this_line += str(field[1]) + '\n'
                        fid.write(this_line)
                    fid.write('\n\n')

                for enum in enums:
                    print enum
                    fid.write(enum + '\n\n\n')

            if line.startswith('// START MANUAL DEFS'):
                write_line = True

            if write_line:
                fid.write(line)