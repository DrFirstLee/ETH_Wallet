## https://github.com/app-generator/flask-volt-dashboard

## blockchain node start :
## geth --datadir /home/private-geth/data --networkid 5777 --port 30303 -http --http.addr "0.0.0.0" --http.port 8505 --http.corsdomain "*" --allow-insecure-unlock --http.api personal,eth,net,web3,miner console 2>> /home/private-geth/error.log


cd /home/site/flask-volt-dashboard
source env/bin/activate
flask run --host=0.0.0.0 --port=5000
