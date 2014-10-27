import os
import re
import shutil
import codecs

wd = '/home/snordhoff/tmp/doc2tex'
lspskeletond = '/home/snordhoff/versioning/git/langsci/latex/skeleton'


def convert(fn):
    print "converting %s" %fn
    odtfn = False
    os.chdir(wd)
    if fn.endswith("docx"):
	odtfn = fn.replace("docx","odt") 
	syscall = """soffice --headless --convert-to odt "%s"  """ %fn
	print syscall
	os.system(syscall)
    if fn.endswith("doc"):
	odtfn = fn.replace("doc","odt")
	syscall = """soffice --headless --convert-to odt "%s"  """ %fn
	print syscall
	os.system(syscall)
    if fn.endswith("odt"):
	odtfn = fn 
    if odtfn == False:
	return False
    texfn = odtfn.replace("odt","tex")
    w2loptions = ("-clean",
    "-wrap_lines_after=0",
    "-multilingual=false", 
    #floats
    "-simple_table_limit=10"
    "-use_supertabular=false",
    "-float_tables=true", 
    "-float_figures=true", 
    "-use_caption=true", 
    '-image_options="width=\\textwidth"',
    #input
    "-inputencoding=utf8",
    "-use_tipa=false", 
    "-use_bibtex=true", 
    "-ignore_empty_paragraphs=true",
    #"-ignore_double_spaces=true", 
    #formatting
    "-formatting=convert_most",
    "-use_color=false",
    "-page_formatting=ignore_all",
    "-use_hyperref=true",
    #"-no_preamble=true"
    )
    syscall = "w2l {} {} {}".format(" ".join(w2loptions), odtfn, texfn)
    print syscall
    os.system(syscall)
    w2lcontent = open(texfn).read().decode('utf8')
    preamble, text = w2lcontent.split(r"\begin{document}")
    text = text.split(r"\end{document}")[0] 
    preamble=preamble.split('\n')
    newcommands = '\n'.join([l for l in preamble if l.startswith('\\newcommand') or l.startswith('\\renewcommand')])
    newpackages = '\n'.join([l for l in preamble if l.startswith('\\usepackage')])
    newcounters = '\n'.join([l for l in preamble if l.startswith('\\newcounter')])        
    return Document(newcommands, newpackages, newcounters, text)
    
class Document:
    def __init__(self, commands, packages, counters, text):
	self.commands = commands
	self.packages = packages
	self.counters = counters
	self.text = text
	self.modtext = self.getModtext()
	
    def ziptex(self): 
	localskeletond = os.path.join(wd,'skeleton')
	try:
	   shutil.rmtree(localskeletond)
	except os.IOError:
	    pass
	shutil.copytree(lspskeletond, localskeletond)
	os.chdir(localskeletond)
	localcommands = open('localcommands.sty','a')
	localpackages = open('localpackages.sty','a')
	localcounters = open('localcounters.sty','a') 
	content =   codecs.open('chapters/filename.tex','w', encoding='utf-8') 
	contentorig =   codecs.open('chapters/filenameorig.tex','w', encoding='utf-8')  
	localcommands.write(self.commands)
	localcommands.close()
	localpackages.write(self.packages)
	localpackages.close()
	localcounters.write(self.counters)
	localcounters.close()
	content.write(self.modtext)
	content.close()
	contentorig.write(self.text)
	contentorig.close()
	os.chdir(wd)
	zipfn = 'test'
	shutil.make_archive(zipfn, 'zip', localskeletond)
	#move to weblocation
	#return weblocation
	
	
	
    def getModtext(self):
	modtext = self.text
	explicitreplacements = (("{\\textquoteleft}","`"),
				("{\\textquotedblleft}","``"), 
				("{\\textquoteright}","'"),
				("{\\textquotedblright}","''"),
				("{\\textquotesingle}","'"),
				("{\\textquotedouble}",'"'),
				("\\textstyleVernacularWord","\\emph"),
				("\\textstyleGloss","\\textsc"),
				("\\par}","}"),
				("\\clearpage","\n"),
				("\\begin","\n\\begin"),
				("\\end","\n\\end"),
				("\ "," "),
				("supertabular","tabular"),
				("\\begin{center}","\\begin{table}\\centering"),
				("\\end{center}","\\caption{}\n%\\label{}\n\\end{table}\n"),
				(" }","} ")
			    )    
	yanks =  ( ("\\begin{flushleft}","\\end{flushleft}","\\centering","\\tablehead{}","\\textstylefootnotereference","\\textstylepagenumber","\\textstyleCharChar","\\textstyleIPA","\\textstyleInternetlink","\\textstylefootnotereference","\\textstyleFootnoteTextChar","\\textstylepagenumber","\\textstyleappleconvertedspace","\\pagestyle{Standard}","\-","\\hline")
			    )
	for old, new in explicitreplacements:
	    modtext = modtext.replace(old,new)
	    
	for y in yanks:
	    modtext = modtext.replace(y,'')
	
	#remove marked up white space
	modtext = re.sub("\\text(it|bf|sc)\{( *)\}","\\2",modtext)  
	
	#remove explicit table widths
	modtext = re.sub("m\{-?[0-9.]+in\}","l",modtext)  
	modtext = re.sub("l\|","l",modtext)
	modtext = re.sub("\|l","l",modtext)
    
	#remove explicit shorttitle for sections
	modtext = re.sub("\\\\(sub)*section(\[.*?\])\{(\\text[bfmd][bfmd])\?(.*)\}","\\\\1section{\\4}",modtext) 
	#                        several subs | options       formatting           title ||   subs      title
	#move explict section number to end of line and comment out
	modtext = re.sub("section\{([0-9\.]+ )(.*)","section{\2 %\1/",modtext)
	modtext = re.sub("section\[.*?\]","section",modtext)
	#                                 number    title         title number
	modtext = re.sub("[\n ]*&[ \n]*",' & ',modtext)
	modtext = re.sub("\n*\\\\\\\\\n*",'\\\\\\\\\n',modtext) 
	#bib
	modtext = re.sub("\(([A-Z][a-z]+) +et al\.  +([12][0-9]{3}[a-z]?): *([0-9,-]+)\)","\\citep[\\3]{\\1EtAl\\2}",modtext)
	modtext = re.sub("\(([A-Z][a-z]+) +([12][0-9]{3}[a-z]?): *([0-9,-]+)\)","\\citep[\\3]{\\1\\2}",modtext)
	modtext = re.sub("\(([A-Z][a-z]+) +et al\. +([12][0-9]{3}[a-z]?)\)","\\citep{\\1EtAl\\2}",modtext)
	modtext = re.sub("\(([A-Z][a-z]+) +([12][0-9]{3}[a-z]?)\)","\\citep{\\1\\2}",modtext)
	#citet
	modtext = re.sub("([A-Z][a-z]+) +et al. +\(([12][0-9]{3}[a-z]?): *([0-9,-]+)\)","\\citet[\\3]{\\1EtAl\\2}",modtext)
	modtext = re.sub("([A-Z][a-z]+) +\(([12][0-9]{3}[a-z]?): *([0-9,-]+)\)","\\citet[\\3]{\\1\\2}",modtext)
	modtext = re.sub("([A-Z][a-z]+) +et al. +\(([12][0-9]{3}[a-z]?)\)","\\citet{\\1EtAl\\2}",modtext)
	modtext = re.sub("([A-Z][a-z]+) +\(([12][0-9]{3}[a-z]?)\)","\\citet{\\1\\2}",modtext)
	#modtext = re.sub("([A-Z][a-z]+) +([12][0-9]{3}[a-z]?)","\\citet{\\1\\2}",modtext)i

	#excamples
	modtext = modtext.replace("\n()", "\n\\ea \n \\gll \\\\\n   \\\\\n \\glt\n\\z\n\n")
	modtext = re.sub("\n\(([0-9]+)\)", """\n\ea%\\1
    \label{ex:\\1}
    \langinfo{}{}\\\\newline
    \\\\gll\\\\newline
	\\\\newline
    \\\\glt
    \z

    """,modtext)
	modtext = re.sub("\\label\{(bkm:Ref[0-9]+)\}\(\)", """ea%\\1
    \label{\\1}
    \langinfo{}{}\\\\newline
    \\\\gll \\\\newline  
	\\\\newline
    \\\\glt
    \z

    """,modtext)
	modtext = modtext.replace("\n *a. ","\n% \\ea\n%\\gll \n%    \n%\\glt \n")
	modtext = modtext.replace("\n *b. ","%\\ex\n%\\gll \\\\\n%    \\\\\n%\\glt \n%\\z\n")    
	modtext = modtext.replace("\n *c. ","%\\ex\n%\\gll \\\\\n%    \\\\\n%\\glt \n%\\z\n")
	modtext = modtext.replace("\n *d. ",r"""
    \ea
    \gll \\
	\\
    \glt 
    \z
    """)
	modtext = modtext.replace(r"\newline",r"\\")
	modtext = modtext.replace(r'\ &','\&')


	modtext = re.sub("Table ([0-9]+)[\.:](.*?)\n","\\\\begin{table}\n\\caption{\\2}\n\\label{tab:\\1}\n\\end{table}",modtext)
	modtext = re.sub("Table ([0-9]+)","\\tabref{tab:\\1}",modtext)
	modtext = re.sub("Figure ([0-9]+)[\.:](.*?)\n","\\\\begin{figure}\n\\caption{\\2}\n\\label{tab:\\1}\n\\end{figure}",modtext)
	modtext = re.sub("Figure ([0-9]+)","\\figref{fig:\\1}",modtext)
	modtext = re.sub("Section ([0-9\.]+)","\\sectref{sec:\\1}",modtext) 
	return modtext
	    
	    
