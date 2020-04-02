while true; do
    date
    git fetch
    git rebase origin/master
    python covid19.py
    git add -f docs/index.html
    git commit -m "Automatic update"
    git push origin HEAD:master
    sleep 300
done