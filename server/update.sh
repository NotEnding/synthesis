#!/bin/bash
logdir=logdir
backdir=$logdir/backup/`date +"%Y-%m-%d"`
if [[ $1 == 'backup' ]]
then
    for file in `ls $logdir | grep '\.log'`;
    do
        mkdir -p $backdir
        cp $logdir/$file $backdir/$file
        echo `date` > $logdir/$file
    done
elif [[ $1 == 'clean' ]]
then
    rm -r `date +"$logdir/backup/%Y-%m-*" -d "-32 days"`
elif [[ $1 == 'check' ]]
then
    . email.sh
    # && python demo.py | grep -v "'code': 404" 2>&1 > /dev/null \
    python demo.py 2>&1 > /dev/null \
        || \
        (bash kill.sh server \
        && bash kill.sh worker \
        && bash setup.sh \
        && sendEmail -f $from \
                     -t $to \
                     -s $server \
                     -o message-content-type=html \
                     -o message-charset=utf-8 \
                     -xu $user \
                     -xp $passwd \
                     -u $title \
                     -m $content )
    # -f 发件人邮箱地址，如from@163.com
    # -t 收件人邮箱地址，如to@qq.com
    # -s 发件人邮箱的smtp服务器地址，如smtp.163.com
    # -o message-content-type=html 邮件内容格式为html
    # -o message-charset=utf-8 邮件内容编码为utf-8
    # -xu 发件人邮箱登陆用户名，如from@163.com
    # -xp 发件人邮箱登录密码
    # -u 邮件标题
    # -m 邮件内容
fi
