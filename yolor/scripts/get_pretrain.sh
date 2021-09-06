curl -c ./cookie -s -L "https://drive.google.com/uc?export=download&id=1WyzcN1-I0n8BoeRhi_xVt8C5msqdx_7k" > /dev/null
curl -Lb ./cookie "https://drive.google.com/uc?export=download&confirm=`awk '/download/ {print $NF}' ./cookie`&id=1WyzcN1-I0n8BoeRhi_xVt8C5msqdx_7k" -o yolor-p6.pt
rm ./cookie

curl -c ./cookie -s -L "https://drive.google.com/uc?export=download&id=1KnkBzNxATKK8AiDXrW_qF-vRNOsICV0B" > /dev/null
curl -Lb ./cookie "https://drive.google.com/uc?export=download&confirm=`awk '/download/ {print $NF}' ./cookie`&id=1KnkBzNxATKK8AiDXrW_qF-vRNOsICV0B" -o yolor-w6.pt
rm ./cookie

curl -c ./cookie -s -L "https://drive.google.com/uc?export=download&id=1jVrq8R1TA60XTUEqqljxAPlt0M_MAGC8" > /dev/null
curl -Lb ./cookie "https://drive.google.com/uc?export=download&confirm=`awk '/download/ {print $NF}' ./cookie`&id=1jVrq8R1TA60XTUEqqljxAPlt0M_MAGC8" -o yolor-e6.pt
rm ./cookie

curl -c ./cookie -s -L "https://drive.google.com/uc?export=download&id=1WX33ymg_XJLUJdoSf5oUYGHAtpSG2gj8" > /dev/null
curl -Lb ./cookie "https://drive.google.com/uc?export=download&confirm=`awk '/download/ {print $NF}' ./cookie`&id=1WX33ymg_XJLUJdoSf5oUYGHAtpSG2gj8" -o yolor-d6.pt
rm ./cookie

curl -c ./cookie -s -L "https://drive.google.com/uc?export=download&id=1NbMG3ivuBQ4S8kEhFJ0FIqOQXevGje_w" > /dev/null
curl -Lb ./cookie "https://drive.google.com/uc?export=download&confirm=`awk '/download/ {print $NF}' ./cookie`&id=1NbMG3ivuBQ4S8kEhFJ0FIqOQXevGje_w" -o yolor_csp_x_star.pt
rm ./cookie

curl -c ./cookie -s -L "https://drive.google.com/uc?export=download&id=1OJKgIasELZYxkIjFoiqyn555bcmixUP2" > /dev/null
curl -Lb ./cookie "https://drive.google.com/uc?export=download&confirm=`awk '/download/ {print $NF}' ./cookie`&id=1OJKgIasELZYxkIjFoiqyn555bcmixUP2" -o yolor_csp.pt
rm ./cookie

curl -c ./cookie -s -L "https://drive.google.com/uc?export=download&id=1xhG0kRH1EX5B9_Iz8gQJb7UNnn_riXi6" > /dev/null
curl -Lb ./cookie "https://drive.google.com/uc?export=download&confirm=`awk '/download/ {print $NF}' ./cookie`&id=1xhG0kRH1EX5B9_Iz8gQJb7UNnn_riXi6" -o ckpt.t7
rm ./cookie