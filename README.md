Description

This is a baseline module for detecting age discrimination in Dutch job advertisements. It is based on observations from a corpus study.
It aims to identify clear cases of age discrimination with high precision. 

Working

The module identifies patterns of explicit age discrimination (advertisements that explicitly ask for young or old people or people of a certain age),
as well as patterns that imply a specific age ('recently finished school', 'close to retirement').
It also distinguishes between strict matches (a sequence of words must occur literally) and more flexible matches (where there may be other terms in between).

The module aims for high precision. In both cases, the pattern includes expressions that indicate that the recruiters are looking for someone of a certain age.
Cases where an age limitation is part of a more complex structure or it the indication is listed among many requested properties are currently not captured.

Exceptions

There are special programs that address unemployment among young or older employees. In these cases, age limitations are allowed. The program scans for such programs being mentioned.
Implicit references to studies and school are allowed in cases of internships. Mentions of an internship are also identified.
Some advertisements ask for 'a starter or more experienced'. The program filters cases that ask for 'X' or 'Y' out and does not mark them as forbidden.

Disclaimer

Many of the decisions taken above are simplifications. This program was built to support a study in communication science and help the researchers identify problematic advertisement.
The strong focus on precision was made at the request of the project financers. We are well aware that this led to significant suffering in recall.
