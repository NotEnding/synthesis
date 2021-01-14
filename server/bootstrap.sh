nohup python server.py >/dev/null  &
sleep 500
ps aux | grep server.py
./run.sh 0 0 person_1
sleep 500
./run.sh 1 1 person_2
sleep 500
ps aux | grep tgpuworker.py
nvidia-smi
python demo.py
