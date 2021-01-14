if [ $# == 3 ]
then
    stid=$1
    edid=$2
    spkid=$3
else
    echo -e 'Usage: $0 <start-gpuid> <end-gpuid> <spkid>'
    exit -1
fi
for i in `seq $1 $2`;do
    nohup python -u tgpuworker.py -l logdir/tgpuworker_$i-$spkid.log -c $i -s $spkid 2>&1 > /dev/null &
done
