echo "BaFA"
python ../../../../src/BaFA.py -g --netname 7x200_best.pth --dataset mnist --relu_transformer box --data_dir mnist_1_brightness_01_001_proof_transfer4 --num_tests 50 --num_post_cons 7

echo "Interval Domain"
python ../../../../src/interval.py -g --netname 7x200_best.pth --dataset mnist --relu_transformer box --data_dir mnist_1_brightness_01_001_proof_transfer4 --num_tests 50
