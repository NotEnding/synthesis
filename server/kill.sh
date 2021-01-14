if [ $# != 1 ]
then
    echo -e 'Something wrong!\n     need one parameter, "server" or "worker" alternatively'
    exit -1
fi

if [ $1 == 'server' ]
then
    ps aux | grep '\<server.py\>' | grep '\<python\>' | awk '{print $2}' | xargs -n1 kill -9
elif [ $1 == 'worker' ]
then
    ps aux | grep '\<tgpuworker.py\>' | grep '\<python\>' | awk '{print $2}' | xargs -n1 kill -9
else
    echo -e 'Wrong kind of parameter, only "server" and "worker" are supported!'
fi
