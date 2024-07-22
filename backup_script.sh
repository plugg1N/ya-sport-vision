tar -czvf back$1.tar.gz *.py chunking Utils/*.py Utils/*.cpp Utils/preprocessors sum/*.py sum/*.ipynb
echo "Created backup with 'backup$1.tar.gz' name"
