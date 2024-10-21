#python ../../../../src/orca.py -p --netname 7x200_best.pth --dataset mnist --relu_transformer zonotope --patch_size 2 --template_method l_infinity --template_domain box --template_layers 0 --num_tests 100

python ../../../../src/benchmarks.py -p --netname 7x200_best.pth --dataset mnist --relu_transformer zonotope --patch_size 2 --template_method l_infinity --template_domain box --template_layers 0 --num_tests 100
