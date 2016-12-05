import os
import sys
import re
import shutil


strictly_red = {}
strictly_orange = {}
flexible_red = {}
flexible_orange = {}

strict_red_age = {}
strict_orange_age = {}
flexible_red_age = {}
flexible_orange_age = {}


def dict_initiation(dictname, filename):

    key = ''
    for line in open(filename, 'r'):
        if '==' in line:
            key = line.split('==')[1]
            dictname[key] = []
        else:
            dictname[key].append(line.rstrip())

def initiate_dicts():
    
    global strictly_red, strictly_orange, flexible_red, flexible_orange

    #TODO: BECOMES STRICT_RED
    dict_initiation(strictly_red, 'strict_red.txt')
    dict_initiation(strictly_orange, 'strict_orange.txt')
    dict_initiation(flexible_red, 'flexible_red.txt')
    dict_initiation(flexible_orange, 'flexible_orange.txt')


def check_final_destinations():

    my_dests = ['strict_reds','strict_oranges','flexible_reds','flexible_oranges']

    for dir in my_dests:
        if not os.path.exists(dir):
            os.makedirs(dir)


def create_first_line():

    global strictly_red, strictly_orange

    firstLine = 'FileId,Aanpak werkloosheid,Stage'

    for k in sorted(strictly_red.keys()):
        firstLine += ',rood-' + k
    
    for k in sorted(strictly_orange.keys()):
        firstLine += ',oranje-' + k


    for k in sorted(flexible_red.keys()):
        firstLine += ',flexrood-' + k
    
    for k in sorted(flexible_orange.keys()):
        firstLine += ',flexoranje-' + k

    return firstLine + '\n'



def initiate_count_dicts():

    global strictly_red, strictly_orange, flexible_red, flexible_orange
    
    
    count_dict = {}
    
    count_dict['unemployment'] = 0
    count_dict['internship'] = 0
    
    count_strict_red = {}
    for k in strictly_red.keys():
        count_strict_red[k] = 0
    count_dict['strictRed'] = count_strict_red

    count_strict_orange = {}
    for k in strictly_orange.keys():
        count_strict_orange[k] = 0
    count_dict['strictOrange'] = count_strict_orange

    count_flexible_red = {}
    for k in flexible_red.keys():
        count_flexible_red[k] = 0
        count_dict['flexibleRed'] = count_flexible_red
    
    count_flexible_orange = {}
    for k in flexible_orange.keys():
        count_flexible_orange[k] = 0
    count_dict['flexibleOrange'] = count_flexible_orange


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



def analyze_file(filename, count_dict):

    global strictly_red, strictly_orange, flexible_red, flexible_orange
    
    global strictly_red_age, strictly_orange_age, flexible_red_age, flexible_orange_age
    
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

    outvalues = ',' + str(count_dict.get('unemployment')) + ',' + str(count_dict.get('internship'))
    red_strict = count_dict.get('strictRed')
    for k in sorted(red_strict.keys()):
        outvalues += ',' + str(red_strict.get(k))
    
    orange_strict = count_dict.get('strictOrange')
    for k in sorted(orange_strict.keys()):
        outvalues += ',' + str(orange_strict.get(k))


    red_flex = count_dict.get('flexibleRed')
    for k in sorted(red_flex.keys()):
        outvalues += ',' + str(red_flex.get(k))

    orange_flex = count_dict.get('flexibleOrange')
    for k in sorted(orange_flex.keys()):
        outvalues += ',' + str(orange_flex.get(k))

    return outvalues




def classify_files(inputdir, outputfile = None):

    if outputfile is None:
        outputfile = 'classifications.csv'
    
    myout = open(outputfile, 'w')
    myout.write(create_first_line())

    for f in os.listdir(inputdir):
        count_dict = initiate_count_dicts()
        values = analyze_file(inputdir + f, count_dict)
        outvalues = create_output_values(count_dict)
        myout.write(f + outvalues + '\n')
        if values[0]:
            shutil.copy(inputdir + f, 'strict_reds/')
        if values[1]:
            shutil.copy(inputdir + f, 'strict_oranges/')
        if values[2]:
            shutil.copy(inputdir + f, 'flexible_reds/')
        if values[3]:
            shutil.copy(inputdir + f, 'flexible_oranges/')





def main(argv=None):

    if argv is None:
        argv = sys.argv

    if len(argv) < 2:
        print('Usage: python red_orange_identification.py inputdir/')
    elif len(argv) < 3:
        initiate_dicts()
        check_final_destinations()
        classify_files(argv[1])
    else:
        initiate_dicts()
        check_final_destinations()
        classify_files(argv[1], argv[2])


if __name__ == '__main__':
    main()