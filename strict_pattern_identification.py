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
        print(x)
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
    counter=0
    for line in open(filename, 'r'):
        newline = line
        for classname, pdict in pattern_dicts.items():
            for k in pdict.keys():
                if k in line.lower():
                    for v in pdict.get(k):
                        if re.match(v, line.lower()):
                            counter+=1
                            rx = re.compile(v)
#                            newline = re.sub(rx, r'\1<span><b>\2</b></span>\3', line.lower())
                            if v.find('agestr')>0:
                                newline = re.sub(rx, r'\g<prestr><span>\g<relstr></span><spanAge><b>\g<agestr></b></spanAge>\g<poststr>',line.lower())
                            else:
                                newline = re.sub(rx, r'\g<prestr><span><b>\g<relstr></b></span>\g<poststr>', line.lower())
                            mycount_dict = count_dict.get(classname)
                            mycount_dict[k] += 1
                            values[classname] = None
        text += newline
    for key in values:
        values[key] = text
    return values

def analyze_file_im(filename, count_dict, pattern_dicts):

    values = {}
    text = ''
    print(filename)
    for line in open(filename, 'r'):
        newline = line

        for classname, pdict in pattern_dicts.items():
            for k in pdict.keys():
                print(classname)
                print("k: "+k)
                if k in line.lower():
                    for v in pdict.get(k):
                        if re.match(v, line.lower()):
                            print(v)
                            rx = re.compile(v)
                            matchObject=re.search(v,line.lower())
                            strfound=matchObject.group()
                            print ("m: "+strfound)
 #                           newline=line.replace(strfound, "<span><b>"+strfound+"</b></span>")
                            newline = re.sub(rx, r'\1<span><b>\2</b></span>\3', line.lower())


#                            print("inter: "+newline)
                            mycount_dict = count_dict.get(classname)
                            mycount_dict[k] += 1
                            values[classname] = None
        text += newline
#        print("n t: "+text)
    for key in values:
        values[key] = text
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
