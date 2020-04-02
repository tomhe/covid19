while true; do
    date
    python covid19.py
    git commit -a -m "Automatic update"
    git push origin HEAD:master
    sleep 300
done