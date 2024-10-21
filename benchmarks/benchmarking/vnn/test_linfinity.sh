python ../../../../src/orca.py -l --netname 5x100_DiffAI.pyt --dataset "mnist" --epsilon "0.1" --relu_transformer zonotope --label 0 --template_layers 2 3 --template_with_hyperplanes 0 --template_domain box --template_dir 5x100_DiffAI_templates_7_0_box_exact_try5_w3.pkl 5x100_DiffAI_templates_9_0_box_exact_w3.pkl --num_tests 1000

#python ../../../../src/orca.py -l --netname 5x100_DiffAI.pyt --dataset "mnist" --epsilon "0.1" --relu_transformer zonotope --label 0 --template_layers 2 3 --template_with_hyperplanes 0 --template_domain box --num_tests 10

