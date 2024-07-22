#!/bin/bash

FILES=(
    "/sum_pipe.py"
    "/micro_stt.py"
    "/micro_chroma.py"
    "/micro_redis.py"
    "/back.py"
)

for file in "${FILES[@]}"; do
    if [[ -f "$file" ]]; then
        echo "Запуск $file..."
        python3 "$file"
    else
        echo "Файл $file не найден."
    fi
done
