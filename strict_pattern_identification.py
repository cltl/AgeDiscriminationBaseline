import os
import sys
import re
import shutil
import argparse
from collections import defaultdict



age_discriminating_categories = ['min','stud','leeftijd_vanaf','leeftijd_bepaald','ouder']



def dict_update(mydict, filename):

    key = ''
    for line in open('patterns/' + filename, 'r'):
        if '==' in line:
            key = line.split('==')[1]
            if key in age_discriminating_categories:
                mydict[key + '_vanaf18ofjonger'] = []
            mydict[key] = []
        else:
            mydict[key].append(line.rstrip())
            if key in age_discriminating_categories and 'agestr' in line:
                mydict[key + '_vanaf18ofjonger'].append(line.rstrip())


def create_first_line(classification_dict):

    firstLine = 'FileId'
    for key in sorted(classification_dict.keys()):
        stage_dicts = classification_dict.get(key)
        for k in sorted(stage_dicts.keys()):
            mydict = stage_dicts.get(k)
            for header in sorted(mydict.keys()):
                firstLine += ',' + header + ' (' + k + ')'

    return firstLine + '\n'


def interpret_config_file(config):

    configurations = {}
    files = []
    counter = 1
    key_name = None
    class_file_dict = {}
    for line in open(config, 'r'):
        if ';' in line:
            if len(files) > 0 and not key_name is None:
                class_file_dict[key_name] = files
                if line.rstrip().endswith(';new;'):
                    configurations[counter] = class_file_dict
                    counter += 1
                    class_file_dict = {}
                files = []
            key_name = line.split(';')[1]
        else:
            files.append(line.rstrip())

    if len(files) > 0 and not key_name is None:
        class_file_dict[key_name] = files
        configurations[counter] = class_file_dict

    return configurations


def initiate_dicts(config):
    '''
    Returns a list of dictionaries with classname and regular expressions attached to it
    :param config: configuration files
    :return: dictionary of classification dictionaries
    '''

    configurations = interpret_config_file(config)
    classification_dicts = {}
    for key, stage_configs in configurations.items():
        stage_dicts = {}

        for classname, files in stage_configs.items():
            mydict = {}
            for filename in files:
                dict_update(mydict, filename)
            stage_dicts[classname] = mydict
        classification_dicts[key] = stage_dicts

    return classification_dicts


def initiate_count_dicts(classification_dicts):

    count_dict = {}

    for key, dicts in classification_dicts.items():
        new_dict = {}
        for dictname, value in dicts.items():
            subdict = {}
            for k in value.keys():
                subdict[k] = 0
            new_dict[dictname] = subdict
        count_dict[key] = new_dict

    return count_dict




def update_age_dict_old(line, myregex, mydict, k):

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


def update_age_dict(age, k, ages_dict):

    if k in ages_dict:
        my_age_count = ages_dict.get(k)
    else:
        my_age_count = defaultdict(int)
    my_age_count[age] += 1
    ages_dict[k] = my_age_count

def analyze_file(filename, count_dicts, pattern_dicts, ages_dict):

    values = {}
    text = ''
    analyze_next = True

    for key in sorted(pattern_dicts.keys()):
        count_dict = count_dicts.get(key)
        if analyze_next:
            pd = pattern_dicts.get(key)
            for line in open(filename, 'r'):
                newline = line
                for classname, pdict in pd.items():
                    for k in pdict.keys():
                        if k.split('_')[0] in line.lower():
                            for v in pdict.get(k):
                                try:
                                    re.match(v, line.lower())
                                except:
                                    print(v, 'THE PROBLEM')
                                if re.match(v, line.lower()):
                                    rx = re.compile(v)
                                    mycount_dict = count_dict.get(classname)
                                    if not '<agestr>' in v:
                                        newline = re.sub(rx, r'\g<prestr><span><b>\g<relstr></b></span>\g<poststr>', newline.lower())
                                        mycount_dict[k] += 1
                                    else:
                                        newline = re.sub(rx, r'\g<prestr><span><b>\g<relstr>\g<agestr></b></span>\g<poststr>', newline.lower())
                                        age = obtain_age(v, line)
                                        update_age_dict(age, k, ages_dict)
                                        if not '_vanaf18ofjonger' in k:
                                            mycount_dict[k] += 1
                                        elif int(age) < 19:
                                            mycount_dict[k] += 1
                                    values[classname] = None
                                    analyze_next = False

                text += newline
        else:
            break

    for key in values:
        values[key] = text
    return values


def obtain_age(pattern, original_line):

    my_match = re.search(pattern, original_line.lower())
    age_expression = my_match.group('agestr')
    age = age_expression.split()[0]

    return age


def analyze_file_per_sentence(filename, count_dict, pattern_dicts):

    values = {}
    text = ''
    analyze_next = True
    for line in open(filename, 'r'):
        newline = line
        for key in sorted(pattern_dicts.keys()):
            if analyze_next:
                pd = pattern_dicts.get(key)
                for classname, pdict in pd.items():
                    for k in pdict.keys():
                        if k in line.lower():
                            for v in pdict.get(k):
                                if re.match(v, line.lower()):
                                    rx = re.compile(v)
                                    newline = re.sub(rx, r'\g<prestr><span><b>\g<relstr></b></span>\g<poststr>', newline.lower())
                                    mycount_dict = count_dict.get(classname)
                                    if not '_vanaf18ofjonger' in k:
                                        mycount_dict[k] += 1
                                    values[classname] = None
                                    analyze_next = False
                                    if '<agestr>' in v:
                                        age = obtain_age(v, line.lower())
                                        if '_vanaf18ofjonger' in k and int(age) < 19:
                                            mycount_dict[k] += 1
            else:
                break
        text += newline

    for key in values:
        values[key] = text
    return values



def create_output_values(count_dict):

    outvalues = ''
    for dkey in sorted(count_dict.keys()):
        stage_dict = count_dict.get(dkey)
        for skey in sorted(stage_dict.keys()):
            mydict = stage_dict.get(skey)
            for k in sorted(mydict.keys()):
                outvalues += ',' + str(mydict.get(k))

    return outvalues

def create_outdirectories(classification_dicts, outdir):


    if not os.path.exists(outdir):
        os.makedirs(outdir)

    for my_dict in classification_dicts.values():
        for k in my_dict.keys():
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
            for secdicts in classification_dicts.values():
                for classname, pdict in secdicts.items():
                    for k in pdict.keys():
                        if k in line.lower():
                            for v in pdict.get(k):
                                try:
                                    if re.match(v, parts[0].lower()):
                                        match += v + ';'
                                except:
                                    print(v)
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
    #FIXME update from above should be included
    for f in os.listdir(inputdir):
        print(f)
        if args.update:
            outdir = args.outdir
            update_regression_test(inputdir + f, outdir + f, classification_dicts, args.matchset)
            shutil.move(outdir + f, inputdir + f)
        else:
            run_regression_test(inputdir + f, classification_dicts)


def run_tests(inputfile):

    for line in open(inputfile, 'r'):
        if line.startswith('=='):
            print('testing ' + line.split('==')[1])
        else:
            parts = line.split('\t')
            testre = parts[1].rstrip()
            if re.match(testre, parts[0]) and parts[0].startswith('FFF'):
                print('False positive', line)
            elif not re.match(testre, parts[0]) and not parts[0].startswith('FFF'):
                print('False negative', line)

def run_unit_tests(args):

    unitdir = args.inputdir

    for f in os.listdir(unitdir):
        run_tests(unitdir + f)

def convert_age_dictionary(ages_dict):

    age_2_expressions = {}
    for expression, agecount in ages_dict.items():
        for age, count in agecount.items():
            if age in age_2_expressions:
                mycounter = age_2_expressions.get(age)
            else:
                mycounter = defaultdict(int)
            mycounter[expression] = count
            age_2_expressions[age] = mycounter
    return age_2_expressions

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

    ages_dict = {}
    for f in os.listdir(inputdir):
        count_dict = initiate_count_dicts(classification_dicts)
        values = analyze_file(inputdir + f, count_dict, classification_dicts, ages_dict)
        outvalues = create_output_values(count_dict)
        myout.write(f + outvalues + '\n')
        #FIXME create marked-up output (values dictionary, key with identified text
        if create_verification_data:
            if len(values) > 0:
                write_outfiles(f, args.outdir, values)

    ages_expression_counts = convert_age_dictionary(ages_dict)
    agesoutputfile = args.ageoutput
    if agesoutputfile is None:
        agesoutputfile = 'expressions_and_ages.csv'
    with open(agesoutputfile, 'w') as agesout:
        agesout.write('age,' + ','.join(sorted(ages_dict.keys())) + '\n')
        for age, expression_dict in ages_expression_counts.items():
            outline = age
            for expression in sorted(ages_dict.keys()):
                if not expression in expression_dict:
                    outline += ',0'
                else:
                    outline += ',' + str(expression_dict.get(expression))
            agesout.write(outline + '\n')




def main():

    parser = argparse.ArgumentParser(description='Aims to identify various forms of age discrimination in job advertisements')
    parser.add_argument('inputdir', metavar='inputdir', help='path to directory containing the job advertisements')
    parser.add_argument('--outputfile', metavar='outputfile', help='path to outputfile providing overall statistics from analysis')
    
    parser.add_argument('--ageoutput', metavar='ageoutput', help='path to outputfile providing counts of the exact ages that were identified')
    parser.add_argument('--outdir', metavar='outputdir', default=None, help='path to output directory (created if does not exist), if placing advertisememts in subdirectories based on their classification is desired (default=None)')
    parser.add_argument('--config', help='path to configuration file (default: local \'config\')', default='config')
    
    parser.add_argument('-u', default=False, action='store_true', dest='unittest', help='calls unit test')
    
    parser.add_argument('-r', default=False, action='store_true', dest='regressiontest', help='calls regression test')
    
    parser.add_argument('--update', default=False, action='store_true', dest='update', help='updates regression test')
    
    parser.add_argument('--matchset', help='path to file with testlines that should be updated (default=None; results in all changes registered)')


    args = parser.parse_args()

    if args.unittest:
        run_unit_tests(args)
    elif args.regressiontest:
        run_regression_tests(args)
    else:
        classify_files(args)





if __name__ == '__main__':
    main()
