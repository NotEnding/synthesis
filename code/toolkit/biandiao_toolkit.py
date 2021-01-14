
###############  toolkit  #####

### 输入:  文本串
### usage:    from biandiao_toolkit import start_biandiao
###           xx,xx=start_biandiao(xx)
### 输出:  文本串 , 变调后的拼音串

import re, os
import jieba
import numpy as np
from pypinyin import pinyin,lazy_pinyin,Style,load_phrases_dict
polyphone=np.load(os.path.join(os.path.dirname(__file__), 'polyphonedict.npy'), allow_pickle=True).item()
load_phrases_dict(polyphone)

chnalplower=[u'A',u'B', u'C', u'D', u'E', u'F', u'G',u'H', u'I', u'J', u'K', u'L', u'M',u'N', u'O', u'P', u'Q', u'R', u'S', u'T', u'U', u'V', u'W', u'X', u'Y', u'Z']
chnalpupper=[u'a',u'b', u'c', u'd', u'e', u'f', u'g',u'h', u'i', u'j', u'k', u'l', u'm',u'n', u'o', u'p', u'q', u'r', u's', u't', u'u', u'v', u'w', u'x', u'y', u'z']
#### 儿化　　＃＃＃＃＃＃＃
def erhua(text,temp):

    # #### fina all 儿  position  ###
    # index=[i for i,word in enumerate(text) if word =='儿']
    # #print(index)

    #####  分词
    # l=[]
    # seg = jieba.cut(text)
    # for i in seg:
    #     l.append(i)
    # ll=[]
    # index=[]
    # ##### 选出结尾为儿的词 ####
    # for i in range(len(l)):
    #     if l[i][-1]=='儿':
    #         ll.append(l[i])
    # ####fina all 儿  position  ###
    # for j in range(len(ll)):
    #     index.append(text.find(ll[j])+len(ll[j])-1)
    index=[]
    for i in range(len(text)):
        if text[i]=='儿':
            index.append(i)


    for i in range(len(index)):
        p=index[i]
        if p!=0:
            if temp[p]=='er2':
                x=temp[p-1]
                y=x[-1]     ####  声调为 1 2 3 4
                w=x[:-1]    ####  pinyin
                t=w+'r'+y   #######  pinyin + r +1 2 3 4
                temp[p-1]=t
                temp[p]='er'
        #temp.remove('er2')
    #### del er2 ###
    # for i in range(len(index)):
    #     del temp[index[i]]
    for i in range(len(temp)):
        if 'er' in temp:
            temp.remove('er')

    return temp


##### 轻声变调 ##########
def qingsheng(text,temp):
    #word=['了','吗','呢','啊','吧','们']
    ##### ABB AAB AA
    # for i in range(len(temp)-1):
    #     if temp[i]==temp[i+1]:
    #         w=temp[i+1]
    #         w=w[:-1]
    #         temp[i+1]=w+'5'


    return temp

 ###### 上声 变调
def shangshen(temp):

    for j in range(len(temp)-1):
        if '3' in temp[j] and  '3' in temp[j+1]:
            x1=temp[j]
            x2=x1.replace('3','2')
            temp[j]=x2
            #temp[j]=str(temp[j]).replace('3','2')


    return temp

 ###### 一 变调
def yibiandiao(text,list_yin):
    #### fina all 一  position  ###
    index=[i for i,word in enumerate(text) if word =='一']
    #print(index)
    charnumber=['零','二','三','四','五','六','七','八','九','十','百','千','万','亿']
    for i in range(len(index)):
        p=index[i]

        if list_yin[p]=='yi1':
            if p<=len(list_yin)-2:   #####    一 位置  不是最后
                if text[p+1] not in charnumber:
                    if '4'  in list_yin[p+1]:    #### 一  在去声前
                        temp=list_yin[p]
                        temp1=temp.replace('1','2')
                        list_yin[p]=temp1
                    else:
                        temp=list_yin[p]
                        temp1=temp.replace('1','4')
                        list_yin[p]=temp1

        elif list_yin[p]=='yi4':
            if p<=len(list_yin)-2:   #####    一 位置  不是最后
                if '4'  in list_yin[p+1]:    #### 一  在去声前
                    temp=list_yin[p]
                    temp1=temp.replace('4','2')
                    list_yin[p]=temp1

        elif list_yin[p]=='yi2':
            if p<=len(list_yin)-2:   #####    一 位置  不是最后
                if '4'  not in list_yin[p+1]:    #### 一  不在去声前
                    temp=list_yin[p]
                    temp1=temp.replace('2','4')
                    list_yin[p]=temp1


    return list_yin

###### 不 变调
def bubiandiao(text,list_yin):
    #### fina all 不  position  ###
    index=[i for i,word in enumerate(text) if word =='不']
    #print(index)

    for i in range(len(index)):
        p=index[i]
        if list_yin[p]=='bu4':
            if p<=len(list_yin)-2:   #####    不 位置  不是最后
                if '4'  in list_yin[p+1]:    #### 不 在去声前
                    temp=list_yin[p]
                    temp1=temp.replace('4','2')
                    list_yin[p]=temp1

        # elif list_yin[p]=='bu2':
        #     if p<=len(list_yin)-2:   #####    不 位置  不是最后
        #         if '4'  in list_yin[p+1]:    #### 不 在去声前
        #             temp=list_yin[p]
        #             temp1=temp.replace('4','2')
        #             list_yin[p]=temp1

    #
    return list_yin

##### 开始 变调   #######
def start_biandiao(line):

    # #####　删除韵律标记　＃２　＃４　
    # line= re.sub(r'#[0-9]', '',line)
    # line=line.strip('\n')

    # #####  pypinyin  ######
    # fayin=[]
    # for i in range(len(line)):
    fayin=lazy_pinyin(line, style=Style.TONE3)
    #     fayin.append(str(duyin[0]))

    #fayin=lazy_pinyin(line, style=Style.TONE3)
    #fayin=[]
    # fayin=fayinstr.split(' ')
    # while '' in fayin:
    #     fayin.remove('')


    # for i in range(len(fayinlist)):
    #     if fayinlist[i][-1].isdigit():

    #         fayin.append(str(fayinlist[i]))
    #     else:
    #         if fayinlist[i]!=' 'and fayinlist[i]!='':
    #             for t in range(len(fayinlist[i])):
    #                 fayin.append(str(fayinlist[i][t]))


        # if fayinlist[i]!=' 'and fayinlist[i]!='':
        #     fayin.append(str(fayinlist[i]))

    #fayin=lazy_pinyin(line, style=Style.TONE3)
    # textlist=text.split(' ')
    # line=[]
    # def contact(sr):
    #     linelist=[]
    #     i=0
    #     while i <len(sr):
    #         if sr[i] in chnalplower or sr[i] in chnalpupper:
    #             temp=''
    #             while sr[i] in chnalplower or  sr[i] in chnalpupper :
    #                 temp+=sr[i]
    #                 i=i+1
    #                 if i >=len(sr):
    #                     break

    #             linelist.append(temp)
    #         else:
    #             linelist.append(sr[i])
    #             i=i+1
    #     return linelist
    # for item in textlist:
    #     srlist=contact(item)
    #     for word in srlist:
    #         line.append(word)

    #### 文本 和 拼音等长
    n=len(line)
    if len(line)==len(fayin):

        #####  轻声中 没有以 5 结尾 加上 5
        for t in range(len(fayin)):
            if fayin[t].isalpha():   ##### 是否只由字母组成
                fayin[t]= fayin[t]+'5'


        if '一' in line and '不' in line :
            ### 一变调
            pinyin=yibiandiao(line,fayin)
            ### 不变调
            pinyin=bubiandiao(line,pinyin)
            ## 轻声变调 ##
            pinyin=qingsheng(line,pinyin)
            ### 上声变调
            pinyin=shangshen(pinyin)

        elif '一' in line and '不' not in line:
            ### 一变调
            pinyin=yibiandiao(line,fayin)
            ## 轻声变调 ##
            pinyin=qingsheng(line,pinyin)
            ### 上声变调
            pinyin=shangshen(pinyin)

        elif '一' not in line and '不'  in line:
            ### 不变调
            pinyin=bubiandiao(line,fayin)
            ## 轻声变调 ##
            pinyin=qingsheng(line,pinyin)

            ### 上声变调
            pinyin=shangshen(pinyin)
        else:
            ## 轻声变调 ##
            pinyin=qingsheng(line,fayin)
            ### 上声变调
            pinyin=shangshen(pinyin)

        #####  儿化 ######
        if '儿' in line:
            pinyin=erhua(line,pinyin)
    else:
        #print('text length not equals pinyin length ',idsr)
        pinyin=fayin
    #### lisr to str
    str_pinyin=" ".join(pinyin)
    return line, str_pinyin



# sr='小饭碗儿，真好玩儿，红花儿绿叶儿镶金边儿，中间儿还有个小红点儿。'
# sr,pinyin=start_biandiao(sr)
# print(pinyin)

# with open('segment_utterances_polypinyin.txt','r') as p:
#     with open('segment_biandiao_result.txt','w') as f:
#         for n ,line in  enumerate(p):
#             idsr,text,pinyin=line.split('|')
#             # flag=line[0:7]
#             # sr=line[7:]
#             # fayin=lazy_pinyin(sr, style=Style.TONE3)
#             # line_yin=" ".join(fayin)
#             # p.write(flag+line_yin+'\n')
#             sr,pinyin=start_biandiao(text,pinyin)
#             #line_pinyin=" ".join(pinyin)
#             f.write(idsr+' '+pinyin+'\n')

# with open('/home/yyg/DATA/biandiao/segment_utterances_polypinyin.txt','r') as f:
#     with open('/home/yyg/DATA/biandiao/segment_biandiao_result.txt','w') as p:
if __name__ == "__main__":
    with open('segment_utterances_polypinyin.txt','r') as f:
        with open('segment_biandiao_result.txt','w') as p:
            for n ,line in  enumerate(f):
    #             flag=line[0:7]
    #             sr=line[7:]
    #             fayin=lazy_pinyin(sr, style=Style.TONE3)
    #             line_yin=" ".join(fayin)
    #             p.write(flag+line_yin+'\n')
    #             sr,pinyin=start_biandiao(sr)
    #             #line_pinyin=" ".join(pinyin)
    #             p.write(flag+pinyin+'\n')
    #             #print(par)
                line=line.strip('\n')

                #line='101689_0_s|大家知道啊,「得到」APP boy有非常严格的品控标准,|da4 jia1 zhi1 dao4 a5 ,「 de2 dao4 」APP you3 fei1 chang2 yan2 ge2 de5 pin3 kong4 biao1 zhun3 ,'
                idsr,text,pinyin=line.split('|')
                # flag=line[0:7]
                # sr=line[7:]
                # fayin=lazy_pinyin(sr, style=Style.TONE3)
                # line_yin=" ".join(fayin)
                # p.write(flag+line_yin+'\n')

                sr,pinyin=start_biandiao(text)
                #line_pinyin=" ".join(pinyin)
                p.write(idsr+' '+pinyin+'\n')
