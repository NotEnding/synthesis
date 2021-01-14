###  text normalization  #######
### input:  text
### usage:    from textnormal import text_normalization
###           xx=text_normalization(xx)
### output: normalization text 

#!/usr/bin/env python
import string, sys, os
import gzip, re
import unicodedata
import math
#import jieba.posseg as pseg
#import pynlpir
#pynlpir.open()

###  Symbol definitions

# mapping from 0, 1, ..., 9 to chinese character
digits={u'0':u'零', u'1':u'一', u'2':u'二', u'3':u'三', u'4':u'四', u'5':u'五', u'6':u'六', u'7':u'七', u'8':u'八', u'9':u'九'}
# mapping from 10, 10^2, 10^3, 10^4, 10^8 to chinese characters
tens=[u'', u'十', u'百', u'千']
thousds=[u'', u'万', u'亿', u'兆']
number=['0','1','2','3','4','5','6','7','8','9']


units=[(u'μg/m3',u'微克每立方米'),(u'w/m·k',u'米开尔文每瓦'),(u'mhz',u'兆赫兹'),(u'ghz',u'千兆赫兹'),
(u'khz',u'千赫兹'),(u'/㎡',u'每平方米'),(u'mbps',u'兆比特每秒'),(u'mg/kg',u'毫克每千克'),(u'kbps',u'千比特每秒'),(u'mb/s',u'兆每秒'),
(u'km/h',u'千米每小时'),(u'g/kg',u'克每千克'),(u'mah',u'毫安时'),(u'kwh',u'千瓦时'),
(u'm/s',u'米每秒'),(u'km2',u'平方千米'),(u'㎞2',u'平方千米'),
(u'km',u'千米'),(u'cm',u'厘米'),(u'mm',u'毫米'),(u'nm',u'纳米'),(u'μm',u'微米'),(u'db',u'分贝'),
(u'ml',u'毫升'),(u'gb',u'千兆字节'),
(u'hz',u'赫兹'),
(u'kw',u'千瓦'),(u'mw',u'兆瓦'),(u'mg',u'毫克'),
(u'kg',u'千克'),(u'm3',u'立方米'),(u'㎡',u'平方米'),(u'ｍg',u'毫克'),
(u'm',u'米'),(u'g',u'克'),
(u'm3',u'立方米'),(u'°',u'度'),(u'w',u'瓦')]
# (u'×',u'乘'),(u'+',u'加'),
# (u'<','小于'),(u'>','大于')]
# Chinese coded English letters and numbers
chnalpupper=[u'a',u'b', u'c', u'd', u'e', u'f', u'g',u'h', u'i', u'j', u'k', u'l', u'm',u'n', u'o', u'p', u'q', u'r', u's', u't', u'u', u'v', u'w', u'x', u'y', u'z']
chnalplower=[u'A',u'B', u'C', u'D', u'E', u'F', u'G',u'H', u'I', u'J', u'K', u'L', u'M',u'N', u'O', u'P', u'Q', u'R', u'S', u'T', u'U', u'V', u'W', u'X', u'Y', u'Z']
chnnumber=[u'0', u'1', u'2', u'3', u'4', u'5', u'6', u'7', u'8', u'9']

chinese_character=[u'零', u'一', u'二', u'三', u'四', u'五', u'六', u'七',u'八', u'九',u'十', u'百', u'千',u'万', u'亿', u'兆']

chinese_date={'日','年','月','号','元'}
char={u'=':u'等于',u'<':u'小于',u'＜':u'小于',u'>':u'大于',u'＞':u'大于',u'+':u'加',u'＋':u'加',u'*':u'乘',u'×':u'乘',u'￥':u'元',
u'=':u'等于',u'$':u'美元',u'￡':u'英镑',u'℃':u'摄氏度',u'°C':u'摄氏度',u'℉':u'华氏度',
u'€':u'欧元',u'°':u'度',u'′':u'分',u'\'':u'分',u'″':u'秒',
u'α':u'阿尔法',u'β':u'贝塔',u'γ':u'伽玛',u'δ':u'德尔塔',u'ε':u'艾普西龙',u'η':u'依塔',u'θ':u'西塔',u'λ':u'拉姆达',
u'μ':u'缪',u'ν':u'拗',u'π':u'派',u'σ':u'西格玛',u'ρ':u'柔',u'τ':u"套",u'ω':u"欧米伽",u'ψ':u"普赛",u'χ':u"器",
u'υ':u'宇普西龙'
}
###,u'ф':u'佛爱'

''' 
Functions
'''

pat_call=re.compile(u'((打120)|(打110)|(打119)|(打911)|(打12306)+)')

pat_year=re.compile(u'(([^0-9]|^)[0-9]{4}年)') # .{1,4}year
pat_year4=re.compile(u'([2][0-9]{3})')

pat_monthday=re.compile(u'([0-1]?[0-9][.][0-3]?[0-9][-][0-1]?[0-9][.][0-3]?[0-9])')
pat_years=re.compile(u'([0-9]{4}[-|~|/|—][0-9]{2,4})')
pat_time=re.compile(u'(([0-1][0-9]|[2][0-3])+[:|：]+([0-5][0-9])+[:|：]+([0-5][0-9]))')
#pat_hourmin=re.compile(u'(([0-1][0-9]|[2][0-3])+[:]+([0-5][0-9]))')
pat_later=re.compile(u'([0-9]{2}后)')
pat_rate=re.compile(u'([0-9]+([.][0-9]+)?[:|∶|：][0-9]+([.][0-9]+)?)')
pat_hour_min=re.compile(u'([0-9]{1,2}[:|∶|：][0-9]{1,2})')
pat_rate_two=re.compile(u'([0-9]{1,2}[-][0-9]{1,2})')
pat_phone=re.compile(r'(\(?[0-9]{3,4}\)?[-|/|—]?[0-9]{3,4}[-|—]?[0-9]{1,10})')
#pat_phone=re.compile(u'([0-9]{3,4}[-|/|—]?[0-9]{3,4}[-|—]?[0-9]{1,4})')
#pat_phone=re.compile(r'(?[0-9]{3,4}[)-]?[0-9]{7,8}')

pat_date= re.compile(r'([1-9][\d]{3}[\-\/\.](1[012]|[0]?[1-9])[\-\/\.]([12][0-9]|3[01]|[0]?[1-9]))')

pat_letternumber=re.compile(u'([a-zA-z]+[-/]?([a-zA-z]+)?[-]?[0-9]+[-/.]?[0-9]+)')
pat_numberletter=re.compile(u'([-]?[0-9]+[-/.]?[0-9]+[-]?[a-zA-z]+)')

pat_mark=re.compile(u'([0-9]{1,4}/[0-9]{1,4})')

#pat_mark=re.compile(u'([0-9]{1,2}/[0-9]{1,2})')
pat_percent=re.compile(r'(([0-9]+)(\.[0-9]+)?[‰%％])')
pat_decimal=re.compile(r'(([0-9]+)\.([0-9]+)+)')


pat_number=re.compile(u'(([0-9]+)(\.[0-9]+)?)')

def strQ2B(ustring):
    """全角转半角"""
    rstring = ""
    for uchar in ustring:
        inside_code=ord(uchar)
        if inside_code == 12288:                              #全角空格直接转换            
            inside_code = 32 
        elif (inside_code >= 65281 and inside_code <= 65374): #全角字符（除空格）根据关系转化
            inside_code -= 65248

        rstring += chr(inside_code)
    return rstring
    
def strB2Q(ustring):
    """半角转全角"""
    rstring = ""
    for uchar in ustring:
        inside_code=ord(uchar)
        if inside_code == 32:                                 #半角空格直接转化                  
            inside_code = 12288
        elif inside_code >= 32 and inside_code <= 126:        #半角字符（除空格）根据关系转化
            inside_code += 65248

        rstring += chr(inside_code)
    return rstring
 
def qqcom(sr):

	pattern=re.compile(u'([0-9]+@qq.com)')
	ressr=u''
	resid=0
	for mt in pattern.finditer(sr):
	
		oldsr=sr[mt.start(1):mt.end(1)]
		ressr+=sr[resid:mt.start(1)]
		newsr=u''
		newsr+=procNumberString(oldsr)
		newsr=newsr.replace('@','艾特').replace('.','点')	
		if newsr!=oldsr:
			ressr+=newsr
		else:
			ressr+=oldsr
		resid=mt.end(1)

	if resid<len(sr):
		ressr+=sr[resid:]

	return ressr
def com163(sr):

	pattern=re.compile(u'([0-9]+@[0-9]+.com)')
	ressr=u''
	resid=0
	for mt in pattern.finditer(sr):
	
		oldsr=sr[mt.start(1):mt.end(1)]
		ressr+=sr[resid:mt.start(1)]
		newsr=u''
		
		newsr+=procNumberString(oldsr)
		newsr=newsr.replace('@','艾特').replace('.','点')	
		if newsr!=oldsr:
			ressr+=newsr
		else:
			ressr+=oldsr
		resid=mt.end(1)

	if resid<len(sr):
		ressr+=sr[resid:]

	return ressr



###  function ####
def prolatitude(sr):
	pattern=re.compile(u'([0-9]+[°][0-9]+[′][0-9]+[″])')
	ressr=u''
	resid=0
	for mt in pat_mark.finditer(sr):
	
		oldsr=sr[mt.start(1):mt.end(1)]
		ressr+=sr[resid:mt.start(1)]
		newsr=u''
		s1,s2,s3=re.split(r'[^\d]',oldsr)
			
		newsr+=procInteger(s1)+u'度'+procInteger(s2)+u'分'+procInteger(s3)+u'秒'
		
		
		if newsr!=oldsr:
			ressr+=newsr
		else:
			ressr+=oldsr
		resid=mt.end(1)

	if resid<len(sr):
		ressr+=sr[resid:]

	return ressr
	


def temperature(sr):
    ressr=u''
    resid=0
    pattern=re.compile(u'([-]?[0-9]+[.]?[0-9]+摄氏度)')
    for mt in pattern.finditer(sr):
        oldsr=sr[mt.start(1):mt.end(1)]
        ressr+=sr[resid:mt.start(1)]
        newsr=u''
        if '-' in oldsr:
            newsr+=oldsr.replace('-','零下')
        else:
            newsr+=oldsr
        if newsr!=oldsr:
            ressr+=newsr
        else:
            ressr+=oldsr

        resid=mt.end(1)

    if resid<len(sr):
        ressr+=sr[resid:]

    return ressr

def procall(sr):
	ressr=u''
	resid=0
	for mt in pat_call.finditer(sr):
		oldsr=sr[mt.start(1):mt.end(1)]
		ressr+=sr[resid:mt.start(1)]
		newsr=u''

		for ii in range(mt.start(1), mt.end(1)):
			if sr[ii] in digits.keys():
				newsr+=digits[sr[ii]]
			else:
				newsr+=sr[ii]
		newsr=re.sub('一','幺',newsr)
		if newsr!=oldsr:
			ressr+=newsr
		else:
			ressr+=oldsr
		
		resid=mt.end(1)

	if resid<len(sr):
		ressr+=sr[resid:]
	
	return ressr


def chartrans(sr):
	for word in sr:
		if word in char.keys():
			sr=sr.replace(word,char[word])
	
	return sr
def fun(itertext,sr):
    ressr=u''
    resid=0
    for mt in itertext:
        oldsr=sr[mt.start(1):mt.end(1)]
        ressr+=sr[resid:mt.start(1)]
        newsr=u''
        
        for ii in range(mt.start(1), mt.end(1)):
            if sr[ii] in digits.keys():
                newsr+=digits[sr[ii]]
            else:
                newsr+=sr[ii]
        
        if newsr!=oldsr:
            ressr+=newsr
        else:
            ressr+=oldsr
        resid=mt.end(1)
        
    if resid<len(sr):
        ressr+=sr[resid:]
    return ressr

####  '-' to '到' ###

def tocharacter(sr):
	if len(sr)>=3:
			
		index1=sr.find(u'-')
		if index1!=0 and index1!=len(sr)-1:
			if sr[index1-1] in chinese_character and sr[index1+1] in chinese_character:
				sr=re.sub(u'-','到',sr)
		index2=sr.find(u'~')
		if index2!=0 and index2!=len(sr)-1:
			#if sr[index2-1] in chinese_character and sr[index2+1] in chinese_character:
			sr=re.sub(u'~','到',sr)
		index３=sr.find(u'-')
		if index３!=0 and index３!=len(sr)-1:
			if sr[index３-1] in chinese_date and sr[index３+1] in chinese_character:
				sr=re.sub(u'-','到',sr)
		index4=sr.find(u'—')
		if index4!=0 and index4!=len(sr)-1:
			if sr[index4-1] in chinese_character and sr[index4+1] in chinese_character:
				sr=re.sub(u'—','到',sr)
		index5=sr.find(u'—')
		if index5!=0 and index5!=len(sr)-1:
			if sr[index5-1] in chinese_date and sr[index5+1] in chinese_character:
				sr=re.sub(u'—','到',sr)
		index6=sr.find(u'－')
		if index6!=0 and index6!=len(sr)-1:
			if sr[index6-1] in chinese_date and sr[index6+1] in chinese_character:
				sr=re.sub(u'－','到',sr)
		index=sr.find(u'～')
		if index!=0 and index!=len(sr)-1:
			#if sr[index-1] in chinese_character and sr[index+1] in chinese_character:
			sr=re.sub(u'～','到',sr)
		word=u'[:|：]'
		index= [m.start() for m in re.finditer(word, sr)] 
		for i in range(len(index)-1):
			if sr[index[i]-1] in chinese_character  and sr[index[i]+1] in chinese_character :
				sr=re.sub(sr[index[i]],'比',sr)
	
	return sr

def promark(sr):
	ressr=u''
	resid=0
	for mt in pat_mark.finditer(sr):
	
		oldsr=sr[mt.start(1):mt.end(1)]
		ressr+=sr[resid:mt.start(1)]
		newsr=u''
		fenzi,fenmu=re.split(r'[^\d]',oldsr)[:2]
			
		newsr+=procInteger(fenmu)+u'分之'+procInteger(fenzi)
		
		
		if newsr!=oldsr:
			ressr+=newsr
		else:
			ressr+=oldsr
		resid=mt.end(1)

	if resid<len(sr):
		ressr+=sr[resid:]

	return ressr

def proletternumber(sr):
	ressr=u''
	resid=0
	for mt in pat_letternumber.finditer(sr):
		oldsr=sr[mt.start(1):mt.end(1)]
		ressr+=sr[resid:mt.start(1)]
		newsr=u''		
		number_sr=procNumberString(oldsr)
		phone_sr=re.sub('一','幺',number_sr)
		newsr+=phone_sr
		newsr=newsr.replace('.','点')
		if newsr!=oldsr:
			ressr+=newsr
		else:
			ressr+=oldsr
		resid=mt.end(1)

	if resid<len(sr):
		ressr+=sr[resid:]

	return ressr

def pronumberletter(sr):
	ressr=u''
	resid=0
	for mt in pat_numberletter.finditer(sr):
		oldsr=sr[mt.start(1):mt.end(1)]
		ressr+=sr[resid:mt.start(1)]
		newsr=u''		
		number_sr=procNumberString(oldsr)
		phone_sr=re.sub('一','幺',number_sr)
		newsr+=phone_sr
		newsr=newsr.replace('.','点')
		if newsr!=oldsr:
			ressr+=newsr
		else:
			ressr+=oldsr
		resid=mt.end(1)

	if resid<len(sr):
		ressr+=sr[resid:]

	return ressr


def prophone(sr):

	ressr=u''
	resid=0
	for mt in pat_phone.finditer(sr):
		oldsr=sr[mt.start(1):mt.end(1)]
		ressr+=sr[resid:mt.start(1)]
		newsr=u''
		oldsr=re.sub(u'[\(\)-]','',oldsr)
		
		
		phone_sr=procNumberString(oldsr)
		phone_sr=re.sub('一','幺',phone_sr)
		## add ,
		ssr=u''
		if len(phone_sr)==10 or len(phone_sr)==11:
			ssr+=phone_sr[0:3]+','+phone_sr[3:7]+','+phone_sr[7:]
		else:
			for i in range(0,len(phone_sr),4):
				if i+4>len(phone_sr):
					ssr+=phone_sr[i:len(phone_sr)]
					
				else:
					ssr+=phone_sr[i:i+4]+','
		newsr+=ssr
		if newsr!=oldsr:
			ressr+=newsr
		else:
			ressr+=oldsr
		resid=mt.end(1)
		

	if resid<len(sr):
		ressr+=sr[resid:]
	
	

	return ressr


def units_transform(sr):
	ressr=u''
	newsr=u''
	for  word in units:
		if str(word[0]) in sr:
			index=sr.find(word[0])
			if sr[index-1].isdigit() or sr[index-1] in chinese_character :
				sr=re.sub(word[0],word[1],sr)

	return sr

def promonthday(sr):
	ressr=u''
	resid=0
	for mt in pat_monthday.finditer(sr):
		oldsr=sr[mt.start(1):mt.end(1)]
		ressr+=sr[resid:mt.start(1)]
		newsr=u''
		month1,day1,month2,day2=re.split(r'[^\d]',oldsr)
		newsr+=procInteger(month1)+u'月'+procInteger(day1)+u'日'	
		newsr+=u'到'+procInteger(month2)+u'月'+procInteger(day2)+u'日'

		if newsr!=oldsr:
			ressr+=newsr
		else:
			ressr+=oldsr
		resid=mt.end(1)

	if resid<len(sr):
		ressr+=sr[resid:]

	return ressr


def proyearmonthday(sr):
	ressr=u''
	resid=0
	for mt in pat_date.finditer(sr):
	#for mt in pat_yearmonthday.finditer(sr):
		oldsr=sr[mt.start(1):mt.end(1)]
		ressr+=sr[resid:mt.start(1)]
		newsr=u''
		year,month,day=re.split(r'[^\d]',oldsr)[:3]
		#year,month,day=oldsr.split(u'-')
		

		for ii in range(len(year)):
			if year[ii] in digits.keys():
				newsr+=digits[year[ii]]
			else:
				newsr+=year[ii]
		sr_month=procInteger(month)
		if len(sr_month)=='2' and sr_month[0]=='零':
			sr_month=sr_month[1:]

		newsr+=u'年'+procInteger(month)+u'月'
		#sr_day=procInteger(day)
		newsr+=procInteger(day)+u'日'
		
		if newsr!=oldsr:
			ressr+=newsr
		else:
			ressr+=oldsr
		resid=mt.end(1)

	if resid<len(sr):
		ressr+=sr[resid:]

	return ressr

# def replaceComments(sr):
# 	while pat_comments.search(sr):
# 		sr=pat_comments.sub(u'', sr)
# 	return sr
# wordlist=pynlpir.segment(sr,pos_tagging=True, pos_names='parent', pos_english=False)
    # for i  in range(len(wordlist)-1):
    #     match = pattern.findall(wordlist[i][0])
    #     if match:
    #         if wordlist[i+1][1] not in dictword:
    #             text=procNumberString(wordlist[i][0])
    #             sr=sr.replace(wordlist[i][0],text)
def timefun(sr):
    newsr=u''
    char1,char2=re.split(u':',sr)
    newsr+=procInteger(char1)+u'点'
    temp=procInteger(char2)
    if temp=='零':
        ressr=newsr
    else:
        ressr=newsr+temp+'分'

    return ressr 
def ratefun(sr):
    newsr=u''
    char1,char2=re.split(u':',sr)
    newsr+=procNumber(char1)+u'比'+procNumber(char2)

    return newsr
'''def proratefun(sr):
	ressr=u''
	resid=0
	for mt in pat_rate.finditer(sr):
		n=0
		oldsr=sr[mt.start(1):mt.end(1)]
		ressr+=sr[resid:mt.start(1)]
		newsr=u''
		#index=[i for i,word in enumerate(sr) if word ==oldsr]
		if '.' in oldsr:
			newsr+=ratefun(oldsr)
		else:
			index=sr.find(oldsr)
			sr1=sr[0:index]
			sr2=sr[index:]
			#sr1,sr2=re.split(oldsr,sr)

			wordlist1=pynlpir.segment(sr1,pos_tagging=True, pos_names='parent', pos_english=False)
			wordlist2=pynlpir.segment(sr2,pos_tagging=True, pos_names='parent', pos_english=False)
			if wordlist1[-1][0] ==' ':
				newsr+=timefun(oldsr)
			elif wordlist1[-1][1]=='时间词' or wordlist2[-1][1]=='时间词':
				newsr+=timefun(oldsr)

			elif len(wordlist1) >=2:
				if wordlist1[-1][1]=='时间词':    
					newsr+=timefun(oldsr)
				else:
					newsr+=ratefun(oldsr)
			else:
				newsr+=ratefun(oldsr)
		
		if newsr!=oldsr:
			ressr+=newsr
		else:
			ressr+=oldsr
		resid=mt.end(1)
		n=n+1
		
	if resid<len(sr):
		ressr+=sr[resid:]



	return ressr
	'''

def prorate(sr):
	ressr=u''
	resid=0
	for mt in pat_hour_min.finditer(sr):
	#for mt in pat_rate_two.finditer(sr):
		oldsr=sr[mt.start(1):mt.end(1)]
		ressr+=sr[resid:mt.start(1)]
		newsr=u''
		char1,char2=re.split(r'[^\d]',oldsr)
		#char1,char2=re.split(u'-',oldsr)


		newsr=procInteger(char1)+u'点'+procInteger(char2)
		#newsr=procInteger(char1)+u'比'+procInteger(char2)
		#sr_mins=procInteger(char2)
		# if len(sr_mins)==1 and sr_mins!='零':
		# 	newsr+='零'+sr_mins+u'分'
		# elif len(sr_mins)==1 and sr_mins=='零':
		# 	newsr=newsr
		# else:
		# 	newsr+=sr_mins+u'分'
		if newsr!=oldsr:
			ressr+=newsr
		else:
			ressr+=oldsr
		resid=mt.end(1)
	if resid<len(sr):
		ressr+=sr[resid:]

	return ressr



def protime(sr):

	ressr=u''
	resid=0
	for mt in pat_time.finditer(sr):
		oldsr=sr[mt.start(1):mt.end(1)]
		ressr+=sr[resid:mt.start(1)]
		newsr=u''

		hours,mins,sceonds=oldsr.split(':')

		newsr=procInteger(hours)+u'点'
		sr_mins=procInteger(mins)

		if len(sr_mins)==1 and sr_mins!='零':
			newsr+='零'+sr_mins+u'分'
		else:
			newsr+=sr_mins+u'分'
		sr_sceonds=procInteger(sceonds)
		if len(sr_sceonds)==1 and sr_sceonds!='零':
			newsr+='零'+sr_sceonds+u'秒'
		elif len(sr_sceonds)==1 and sr_sceonds=='零':
			newsr=newsr
		else:
			newsr+=sr_sceonds+u'秒'

		if newsr!=oldsr:
			ressr+=newsr
		else:
			ressr+=oldsr
		resid=mt.end(1)

	if resid<len(sr):
		ressr+=sr[resid:]


	return ressr

def proyears(sr):
	ressr=u''
	resid=0
	
	for mt in pat_years.finditer(sr):
		oldsr=sr[mt.start(1):mt.end(1)]
		ressr+=sr[resid:mt.start(1)]
		newsr=u''
		year1=re.sub(u'[-|～|/|—]','到',oldsr)

		for ii in range(len(year1)):
			if year1[ii] in digits.keys():
				newsr+=digits[year1[ii]]
			else:
				newsr+=year1[ii]
		

		if newsr!=oldsr:
			ressr+=newsr
		else:
			ressr+=oldsr
		resid=mt.end(1)
	if resid<len(sr):
		ressr+=sr[resid:]	
	return ressr
	


def procYear(sr):
	iterlist=pat_year.finditer(sr)
	sr=fun(iterlist,sr)

	# iter_list=pat_year4.finditer(sr)
	# sr=fun(iter_list,sr)

	ressr=u''
	resid=0
	for mt in pat_later.finditer(sr):
		oldsr=sr[mt.start(1):mt.end(1)]
		ressr+=sr[resid:mt.start(1)]
		newsr=u''
		
		for ii in range(mt.start(1), mt.end(1)):
			if sr[ii] in digits.keys():
				newsr+=digits[sr[ii]]
			else:
				newsr+=sr[ii]
	
		if newsr!=oldsr:
			ressr+=newsr
		else:
			ressr+=oldsr
		resid=mt.end(1)
	if resid<len(sr):
		ressr+=sr[resid:]

	return ressr

def proc4DigNum(sr):
	ressr=u''
	j=len(sr)-1
	for i in range(0,len(sr)):
		if sr[j]!=u'0':
			ressr=digits[sr[j]]+tens[i]+ressr
		else:
			if ressr==u'': 
				ressr=digits[u'0']
			else:
				if ressr[0]!=digits[u'0']:
					ressr=digits[u'0']+ressr
		j=j-1

	# remove extra 0s at the end
	while len(ressr)>1 and ressr[-1]==digits[u'0']:
		ressr=ressr[:-1]

	return ressr

# different from others, the input is the integer string not the whole sentence
def procInteger(sr):
	# too long, convert bit by bit
	if len(sr)>16:
		return procNumberString(sr)

	oldsr=sr
	ressr=u''
	i=0
	curlen=len(oldsr)
	while curlen>0:
		if curlen>=4:
			cursr=proc4DigNum(oldsr[-4:])
			oldsr=oldsr[:-4]
		else:
			cursr=proc4DigNum(oldsr)
			oldsr=u''
		if cursr!=digits[u'0']:
			ressr=cursr+thousds[i]+ressr
		else:
			if ressr==u'':
				ressr=cursr
			else:
				if ressr[0]!=digits[u'0']:
					ressr=digits[u'0']+ressr
		i=i+1
		curlen=len(oldsr)

	# convert begining "one ten" to "ten"
	if len(ressr)>=2 and ressr[:2]==u'一\u5341':
		ressr=ressr[1:]

	# remove extra 0s at the end
	while len(ressr)>1 and ressr[-1]==digits[u'0']:
		ressr=ressr[:-1]

	# remove extra 0s at the beginning
	while len(ressr)>1 and ressr[0]==digits[u'0']:
		ressr=ressr[1:]

	return ressr

#####  number  series ###
def procNumberString(sr):
	newsr=u''
	for ii in range(0, len(sr)):
		if sr[ii] in number:
			newsr=newsr+digits[sr[ii]]
		# elif sr[ii].isalpha():

		# 	newsr=newsr+sr[ii]
		else:
			newsr=newsr+sr[ii]
			#newsr=newsr
	return newsr

#####   include % ‰ ####
def procPercent(sr):
	debug=False
	ressr=u''
	resid=0
	for mt in pat_percent.finditer(sr):
		ressr+=sr[resid:mt.start(1)]

		oldsr=mt.group(1)
		intpart=mt.group(2)
		decpart=mt.group(3)
		if oldsr[-1]==u'%':
			newsr=u'百分之'+procInteger(intpart)
		elif oldsr[-1]==u'％': 
			newsr=u'百分之'+procInteger(intpart)
		elif oldsr[-1]==u'‰':
			newsr=u'千分之'+procInteger(intpart)
		else:
			print ('Error in converting percentages!')
			sys.exit(1)
		if decpart != None:
			newsr+=u'点'+procNumberString(decpart[1:])
		

		ressr+=newsr
		resid=mt.end(1)

	if resid<len(sr):
		ressr+=sr[resid:]

	return ressr

####    include number #####
def procNumber(sr):
	debug=False
	ressr=u''
	resid=0
	for mt in pat_number.finditer(sr):
		ressr+=sr[resid:mt.start(1)]

		oldsr=mt.group(1)
		intpart=mt.group(2)
		decpart=mt.group(3)
		if debug: print (u'####'+oldsr)
		newsr=procInteger(intpart)
		if decpart != None:
			newsr+=u'点'+procNumberString(decpart[1:])
		if debug: print (u'===='+newsr)

		ressr+=newsr
		resid=mt.end(1)

	if resid<len(sr):
		ressr+=sr[resid:]

	return ressr
'''
def segment(sr):
	pattern = re.compile(u'([0-9]{3,8})')
	ressr=u''
	resid=0
	dictword=['名词']
	for mt in pattern.finditer(sr):
		n=0
		oldsr=sr[mt.start(1):mt.end(1)]
		ressr+=sr[resid:mt.start(1)]
		newsr=u''

		index=sr.find(oldsr)
		sr1=sr[0:index]
		sr2=sr[index:]
		#sr1,sr2=re.split(oldsr,sr)

		wordlist1=pynlpir.segment(sr1,pos_tagging=True, pos_names='parent', pos_english=False)
		wordlist2=pynlpir.segment(sr2,pos_tagging=True, pos_names='parent', pos_english=False)
		if wordlist1[-1][0] !=' ':
			if wordlist1[-1][1] in dictword:    
				newsr+=procNumberString(oldsr)
			
			else:
				newsr+=oldsr
		else:
			newsr+=oldsr		
		# elif len(wordlist1) >=2:
		# 	if wordlist1[-1][0]=='标点符号':    
		# 		newsr+=procNumberString(oldsr)
		# 	else:
		# 		newsr+=ratefun(oldsr)
		
		if newsr!=oldsr:
			ressr+=newsr
		else:
			ressr+=oldsr
		resid=mt.end(1)
		n=n+1
        
	if resid<len(sr):
		ressr+=sr[resid:]



    # dictword=['m','量词']
    # words = pseg.cut(sr)
    # wordlist=[]
    # flaglist=[]
    # for word, flag in words:
    #     wordlist.append(word)
    #     flaglist.append(flag)
    # for i in range(len(wordlist)-1):
    #     if wordlist[i].isdigit():
    #         # if flaglist[i+1]=='m':
    #         #     text=procNumber(wordlist[i])
    #         #     sr=sr.replace(wordlist[i],text)
    #         if flaglist[i+1]=='t':
    #             text=procNumberString(wordlist[i])
    #             sr=sr.replace(wordlist[i],text)
    #ressr=sr
	return ressr
	'''
def mei(sr):
    index=[i for i,word in enumerate(sr) if word ==u'/']
    n=len(sr)-1
    for i in range(len(index)):
        if index[i] >0 and index[i]<n:
            if  sr[index[i]-1] not in chnalpupper or sr[index[i]+1] not in chnalpupper:
            #     sr=sr.replace(u'/','')
            # else:
                sr=sr.replace(u'/','每')
    return sr 

def replace(sr):
    pattern=re.compile(u'([0-9]x[0-9])')
    match=pattern.findall(sr)
    if match:
        sr=sr.replace('x','*')
    # patternsub=re.compile(u'([0-9]-[0-9])')
    # match=patternsub.findall(sr)
    # if match:
    #     sr=sr.repace('-','减')
    return sr
def pronumbervalues(sr):
	pattern=re.compile(u'(([0-9]{1,3}[,])?([0-9]{1,3}[,])?[0-9]{1,3}[,][0-9]{3})')
	ressr=u''
	resid=0
	for mt in pattern.finditer(sr):
		oldsr=sr[mt.start(1):mt.end(1)]
		ressr+=sr[resid:mt.start(1)]
		newsr=u''
		oldsr=oldsr.replace(',','')
		newsr=procInteger(oldsr)
		
		if newsr!=oldsr:
			ressr+=newsr
		else:
			ressr+=oldsr
		resid=mt.end(1)
        
	if resid<len(sr):
		ressr+=sr[resid:]
	return ressr

### car number cconvert
def carnumber(sr):
	carstring=re.compile(u'([京津沪渝冀豫云辽黑湘皖鲁新苏浙赣鄂桂甘晋蒙陕吉闽贵粤青藏川宁琼使领a-z]{1}[a-z]{1}[警京津沪渝冀豫云辽黑湘皖鲁新苏浙赣鄂桂甘晋蒙陕吉闽贵粤青藏川宁琼]{0,1}[a-z0-9]{4}[a-z0-9挂学警港澳]{1})')
	ressr=u''
	resid=0
	for mt in carstring.finditer(sr):
		oldsr=sr[mt.start(1):mt.end(1)]
		ressr+=sr[resid:mt.start(1)]
		newsr=u''
		#### 半角转全角 
		newsr+=strB2Q(oldsr)
		if newsr!=oldsr:
			ressr+=newsr
		else:
			ressr+=oldsr
		resid=mt.end(1)
        
	if resid<len(sr):
		ressr+=sr[resid:]
	return ressr

###### start text normalization ######

def text_normalization(sr):
	#### 把字符串全角转半角  
	sr=strQ2B(sr)
	sr=sr.replace('\n','')
	#sr=line.replace(' ','')
	
	sr = sr.replace('，',',').replace('？','?').replace('。','.').replace('！','!').replace('--','-')
	#sr=sr.replace('《',' ').replace('》',' ').replace('：',':')#.replace('“','"').replace('”','"')
	sr=sr.replace('—','-').replace('－','-').replace('～','~').replace('／','/').replace('④','')
	sr=sr.replace('∶',':').replace('℃','摄氏度').replace('°C','摄氏度').replace('℉','华氏度')
	sr=sr.lower()
	
	if sr!=u'':
		#sr=unicodedata.normalize('NFKC', sr)
		####  such as cm ###
		sr=replace(sr)
		par=chartrans(sr)
		#par=units_transform(par)
		par=temperature(par)
		###### latitude ###
		#par=prolatitude(par)
		###
		par=qqcom(par)
		par=com163(par)
		#### 2019-04-15	

		par=proyearmonthday(par)
		####   13:32:45 ####
		par=protime(par)
		#par=prorate(par)

		#####  032-7789-3647
		par=prophone(par)

		####  2019 年

		par=proyears(par)
		par=procYear(par)

		par=promonthday(par)
		##### 12:30
		#par=proratefun(par)
		#### 13:40
		par=prorate(par)
		#### 2/3
		par=promark(par)
		#####  %
		par=procPercent(par)
		#####   ######
		par=carnumber(par)
		###    123C or GB123
		par=proletternumber(par)
		par=pronumberletter(par)
		#### call 110
		par=procall(par)
		### 134.5元

		
		par=pronumbervalues(par)

		#par=segment(par)
		par=procNumber(par)
		par=tocharacter(par)
		par=mei(par)

		par=strQ2B(par)
		#par.upper()
		# par = par.replace('，',',').replace('？','?').replace('。','.').replace('！','!')
		#par=par.replace('《',' ').replace('》',' ').replace('：',' ').replace('“',' ').replace('”',' ')

	else:
		par=sr
	if len(par)>35:
		num_utts=math.ceil(len(par)/35)
		per_utt = math.ceil(len(par) / num_utts)
		par = ','.join([par[std: std+per_utt] for std in range(0, len(par), per_utt)])
	
	return par 


#import re 
#from textnormal import text_normalization
# with open('/home/yyg/DATA/transfer/2019-MH1_evaluation.txt','r') as f:
# 	with open('/home/yyg/DATA/transfer/2019_textnor_result.txt','w') as p:
# 		for n ,line in  enumerate(f):
# 			flag=line[0:7]     
# 			sr=line[7:]   
# 			#sr='等于0.000000001'
#             #p.write(line)
# 			par=text_normalization(sr)
# 			p.write(flag+par+'\n')
if __name__=='__main__':
	with open('/home/yyg/DATA/transfer/syn_text','r') as f:
		with open('/home/yyg/DATA/transfer/syn_text_result.txt','w') as p:
			for n ,line in  enumerate(f):
				# flag=line[0:7]     
				# sr=line[7:]   
				#p.write(line)
				line='1017年11月11日辞职的员工薛东来在1017年1月11日到1月14日通过登入中国频道这个平台设置了我公司注册的其中17个域名的转移会员密码'
				if line=='\n' or line=='"\n':
					p.write(line)
				else:

					sr=text_normalization(line)
					p.write(sr+'\n')


