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
#newline = re.sub(rx, r'\1<span><b>\2</b></span>\3', line.lower())
                            newline = re.sub(rx, r'\g<prestr><span><b>\g<relstr></b></span>\g<poststr>', newline.lower())
                            mycount_dict = count_dict.get(classname)
                            mycount_dict[k] += 1
                            values[classname] = None
        text += newline
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


def run_regression_test(inputfile, classification_dicts):

    correct = 0.0
    total = 0.0
    for line in open(inputfile, 'r'):
        if not line.startswith('=='):
            total += 1
            match = ''
            parts = line.split('\t')
            for classname, pdict in classification_dicts.items():
                for k in pdict.keys():
                    if k in line.lower():
                        for v in pdict.get(k):
                            if re.match(v, parts[0].lower()):
                                match += v + ';'
            if len(match) == 0:
                match = 'CLEAN'
                if line.startswith('FFF'):
                    correct += 1
            elif not line.startswith('FFF'):
                correct += 1
            
            if match != parts[1].rstrip():
                print('CHANGED VALUES:', line, match)

    print(correct/total)

def update_regression_test(inputfile, outputfile, classification_dicts, match_set):

    myoutfile = open(outputfile, 'w')
    for line in open(inputfile, 'r'):
        if line.startswith('=='):
            myoutfile.write(line)
        else:
            match = ''
            parts = line.split('\t')
            for classname, pdict in classification_dicts.items():
                for k in pdict.keys():
                    if k in line.lower():
                        for v in pdict.get(k):
                            if re.match(v, parts[0].lower()):
                                match += v + ';'
            if len(match) == 0:
                match = 'CLEAN'

#print(match)
            if match != parts[1].rstrip():
                if not match_set is None:
                    if line in match_set:
                        myoutfile.write(parts[0] + '\t' + match + '\n')
                    else:
                        myoutfile.write(line)
                else:
                    myoutfile.write(parts[0] + '\t' + match + '\n')
            else:
                myoutfile.write(line)

    myoutfile.close()

def run_regression_tests(args):

    classification_dicts = initiate_dicts(args.config)
    inputdir = args.inputdir

    for f in os.listdir(inputdir):
        print(f)
        if args.update:
            outdir = args.outdir
            update_regression_test(inputdir + f, outdir + f, classification_dicts, args.matchset)
            shutil.move(outdir + f, inputdir + f)
        else:
            run_regression_test(inputdir + f, classification_dicts)


def classify_files(args):


    classification_dicts = initiate_dicts(args.config)
    if args.outputfile is None:
        myout = open('classification_output.csv', 'w')
    else:
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





def main():

    parser = argparse.ArgumentParser(description='Aims to identify various forms of age discrimination in job advertisements')
    parser.add_argument('inputdir', metavar='inputdir', help='path to directory containing the job advertisements')
    parser.add_argument('--outputfile', metavar='outputfile', help='path to outputfile providing statistics from analysis')
    parser.add_argument('--outdir', metavar='outputdir', default=None, help='path to output directory (created if does not exist), if placing advertisememts in subdirectories based on their classification is desired (default=None)')
    parser.add_argument('--config', help='path to configuration file (default: local \'config\')', default='config')
    
    parser.add_argument('-u', default=False, action='store_true', dest='unittest', help='calls unit test')
    
    parser.add_argument('-r', default=False, action='store_true', dest='regressiontest', help='calls regression test')
    
    parser.add_argument('--update', default=False, action='store_true', dest='update', help='updates regression test')
    
    parser.add_argument('--matchset', help='path to file with testlines that should be updated (default=None; results in all changes registered)')


    args = parser.parse_args()

    if args.regressiontest:
        run_regression_tests(args)
    else:
        classify_files(args)





if __name__ == '__main__':
    main()
