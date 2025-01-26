echo "ToyNet.pth"
#python ../../../../src/BaFA.py -l --netname ToyNet.pth --dataset "toy" --epsilon "0.1" --relu_transformer zonotope --label 0 --num_tests 10

echo "ToyNetNet.pth"
#python ../../../../src/BaFA.py -l --netname ToyNetNeg.pth --dataset "toy" --epsilon "0.1" --relu_transformer zonotope --label 0 --num_tests 10

echo "CaterinaEx1.pth"
#python ../../../../src/BaFA.py -l --netname CaterinaEx1.pth --dataset "toy" --epsilon "0.1" --relu_transformer zonotope --label 0 --num_tests 10

echo "CaterinaEx2.pth"
#python ../../../../src/BaFA.py -l --netname CaterinaEx2.pth --dataset "toy" --epsilon "0.1" --relu_transformer zonotope --label 0 --num_tests 10

echo "DeepPolyEx.pth"
#python ../../../../src/BaFA.py -l --netname DeepPolyEx.pth --dataset "toy" --epsilon "0.1" --relu_transformer zonotope --label 0 --num_tests 10

echo "MNIST dataset by BaFA"
python ../../../../src/BaFA.py -l --netname 5x100_DiffAI.pyt --dataset "mnist" --epsilon "0.1" --relu_transform box --label 2 --num_post_cons 2

echo "MNIST dataset by Interval Domain"
python ../../../../src/interval.py -l --netname 5x100_DiffAI.pyt --dataset "mnist" --epsilon "0.1" --relu_transform box --label 2


echo "MNIST dataset by ORCA"
#python ../../../../src/orca.py -l --netname fc_5x100.pth --dataset "mnist" --epsilon "0.1" --relu_transform zonotope --label 1 --template_layers 2 3 --template_with_hyperplanes 0 --template_domain box --template_dir 5x100_DiffAI_templates_7_1_box_exact_try5_w3.pkl 5x100_DiffAI_templates_9_1_box_exact_w3.pkl --num_tests 10

#python ../../../../src/orca.py -l --netname 5x100_DiffAI.pyt --dataset "mnist" --epsilon "0.1" --relu_transformer zonotope --label 0 --template_layers 2 3 --template_with_hyperplanes 0 --template_domain box --num_tests 10

