import os
import sys
import re
import shutil
import argparse




def dict_update(mydict, filename):

    key = ''
    for line in open('patterns/' + filename, 'r'):
        if '==' in line:
            key = line.split('==')[1]
            mydict[key] = []
        else:
            mydict[key].append(line.rstrip())


def create_first_line(classification_dict):

    firstLine = 'FileId'

    for k in sorted(classification_dict.keys()):
        mydict = classification_dict.get(k)
        for header in sorted(mydict.keys()):
            firstLine += ',' + header + ' (' + k + ')'

    return firstLine + '\n'


def interpret_config_file(config):

    configurations = {}
    files = []
    key_name = None
    for line in open(config, 'r'):
        if ';' in line:
            if len(files) > 0 and not key_name is None:
                configurations[key_name] = files
                files = []
            key_name = line.split(';')[1]
        else:
            files.append(line.rstrip())

    if len(files) > 0 and not key_name is None:
        configurations[key_name] = files
    return configurations


def initiate_dicts(config):
    '''
    Returns a list of dictionaries with classname and regular expressions attached to it
    :param config: configuration files
    :return: dictionary of classification dictionaries
    '''

    configurations = interpret_config_file(config)
    classification_dicts = {}
    for classname, files in configurations.items():
        mydict = {}
        for filename in files:
            dict_update(mydict, filename)
        classification_dicts[classname] = mydict

    return classification_dicts


def initiate_count_dicts(classification_dicts):

    count_dict = {}

    for dictname, value in classification_dicts.items():
        subdict = {}
        for k in value.keys():
            subdict[k] = 0
        count_dict[dictname] = subdict

    return count_dict




def update_age_dict(line, myregex, mydict, k):

    mymatch = re.match(myregex, line.lower())
    nr_of_groups = line.count('(')
    #find all identified groups
    found = False
    for x in range(1,nr_of_groups + 1):
        foundnumber = mymatch.group(x)
        if isinstance(foundnumber, int):
            if found:
                print('found 2 numbers for', line)
            myval = mydict.get(k)
            if myval is None:
                myval = {}
            if foundnumber in myval:
                myval[foundnumber] += 1
            else:
                myval[foundnumber] = 1


def analyze_file(filename, count_dict, pattern_dicts):

    values = {}
    text = ''
    for line in open(filename, 'r'):
        newline = line
        for classname, pdict in pattern_dicts.items():
            for k in pdict.keys():
                if k in line.lower():
                    for v in pdict.get(k):
                        if re.match(v, line.lower()):
                            rx = re.compile(v)
                            newline = re.sub(rx, r'\1<span><b>\2</b></span>\3', line.lower())
                            mycount_dict = count_dict.get(classname)
                            mycount_dict[k] += 1
                            values[classname] = None
        text += newline
    for key in values:
        values[key] = text
    return values

def analyze_file_old(filename, count_dict):

    
    values = [False, False, False, False]

    for line in open(filename, 'r'):
        if 'aanpak' in line.lower() and ('werkloosheid' in line.lower() or 'werkeloosheid' in line.lower()):
            count_dict['unemployment'] += 1
        elif 'bestrijding' in line.lower() and ('werkloosheid' in line.lower() or 'werkeloosheid' in line.lower()):
            count_dict['unemployment'] += 1
        if 'stage' in line.lower() or 'stagair' in line.lower():
            count_dict['internship'] += 1
        for k in strictly_red.keys():
            if k in line.lower():
                for v in strictly_red.get(k):
                    if re.match(v, line.lower()):
                        red_dict = count_dict.get('strictRed')
                        red_dict[k] += 1
                        values[0] = True
        for k in strictly_orange.keys():
            if k in line.lower():
                for v in strictly_orange.get(k):
                    if re.match(v, line.lower()) and not ' of ' in line:
                        orange_dict = count_dict.get('strictOrange')
                        orange_dict[k] += 1
                        values[1] = True
        for k in flexible_red.keys():
            if k in line.lower():
                for v in flexible_red.get(k):
                    if re.match(v, line.lower()):
                        fred_dict = count_dict.get('flexibleRed')
                        fred_dict[k] += 1
                        values[2] = True
        for k in flexible_orange.keys():
            if k in line.lower():
                for v in flexible_orange.get(k):
                    if re.match(v, line.lower()) and not ' of ' in line:
                        forange_dict = count_dict.get('flexibleOrange')
                        forange_dict[k] += 1
                        values[3] = True
    return values


def create_output_values(count_dict):

    outvalues = ''
    for dkey in sorted(count_dict.keys()):
        mydict = count_dict.get(dkey)
        for k in sorted(mydict.keys()):
            outvalues += ',' + str(mydict.get(k))

    return outvalues

def create_outdirectories(classification_dicts, outdir):


    if not os.path.exists(outdir):
        os.makedirs(outdir)

    for k in classification_dicts.keys():
        if not os.path.exists(outdir + '/' + k):
            os.makedirs(outdir + '/' + k)


def write_outfiles(infilename, outdir, values):

    for val, text in values.items():
        myoutput = open(outdir + '/' + val + '/' + infilename, 'w')
        myoutput.write(text)
        myoutput.close()


def classify_files(args):


    classification_dicts = initiate_dicts(args.config)
    myout = open(args.outputfile, 'w')
    #create outputfiles if outdir is given
    create_verification_data = False
    if not args.outdir is None:
        create_verification_data = True
        create_outdirectories(classification_dicts, args.outdir)
    #FIXME use CSV library
    myout.write(create_first_line(classification_dicts))

    inputdir = args.inputdir

    for f in os.listdir(inputdir):
        count_dict = initiate_count_dicts(classification_dicts)
        values = analyze_file(inputdir + f, count_dict, classification_dicts)
        outvalues = create_output_values(count_dict)
        myout.write(f + outvalues + '\n')
        #FIXME create marked-up output (values dictionary, key with identified text
        if create_verification_data:
            if len(values) > 0:
                write_outfiles(f, args.outdir, values)

       # if values[0]:
       #     shutil.copy(inputdir + f, 'strict_reds/')
       # if values[1]:
       #     shutil.copy(inputdir + f, 'strict_oranges/')
       # if values[2]:
       #     shutil.copy(inputdir + f, 'flexible_reds/')
       # if values[3]:
       #     shutil.copy(inputdir + f, 'flexible_oranges/')





def main():

    parser = argparse.ArgumentParser(description='Aims to identify various forms of age discrimination in job advertisements')
    parser.add_argument('inputdir', metavar='inputdir', help='path to directory containing the job advertisements')
    parser.add_argument('outputfile', metavar='outputfile', help='path to outputfile providing statistics from analysis')
    parser.add_argument('--outdir', metavar='outputdir', default=None, help='path to output directory (created if does not exist), if placing advertisememts in subdirectories based on their classification is desired (default=None)')
    parser.add_argument('--config', help='path to configuration file (default: local \'config\')', default='config')

    args = parser.parse_args()

    classify_files(args)





if __name__ == '__main__':
    main()