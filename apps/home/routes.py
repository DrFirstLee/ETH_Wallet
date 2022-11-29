# -*- encoding: utf-8 -*-
"""
Copyright (c) 2019 - present AppSeed.us
"""

from apps.home import blueprint
from flask import render_template, request, url_for
from flask_login import login_required, login_user, logout_user, current_user
from jinja2 import TemplateNotFound
import requests
import json
import datetime
import pandas as pd

from web3 import Web3

BLOCKCHAIN_ADR = "http://175.45.201.73:8505"
w3 = Web3(Web3.HTTPProvider(BLOCKCHAIN_ADR))

import sqlite3

@blueprint.route('/users_info')
@login_required
def wallet_info():
    print('users_info')
    conn = sqlite3.connect("/home/site/flask-volt-dashboard/apps/db.sqlite3")
    cur = conn.cursor()
    
    # get users info
    user_data = pd.read_sql('SELECT * FROM Users', conn)
    
    # get point info
    def get_points(wallet):
        my_points =  Web3.fromWei(w3.eth.getBalance(wallet), 'ether')
        return my_points
    user_data['points'] = user_data['wallet'].apply(get_points)

    return render_template('home/users_info.html', segment='index', user_data = user_data)


@blueprint.route('/transaction', methods=['GET', 'POST'])
@login_required
def transaction():
    
    # DB connection
    conn = sqlite3.connect("/home/site/flask-volt-dashboard/apps/db.sqlite3")
    cur = conn.cursor()

    if request.method == 'POST':
        print('post')
        print(request.form.to_dict())
        send_form = request.form.to_dict()
        
        # Unlock from_wallet
        w3.geth.personal.unlock_account(send_form['from_wallet'], send_form['from_username'], duration=None)
        
        # Send points
        to_wallet = pd.read_sql(f"SELECT wallet FROM Users WHERE username='{send_form['to_username']}'",conn).wallet.values[0]
        w3.eth.send_transaction({
          'to': to_wallet,
          'from': send_form['from_wallet'],
          'value': Web3.toWei(send_form['to_points'], 'ether')
        })
    

    tot_data = pd.read_sql(f"SELECT * FROM Users", conn)
    total_points = int(sum([Web3.fromWei(w3.eth.getBalance(i), 'ether') for i in w3.eth.accounts]))
    my_points =  Web3.fromWei(w3.eth.getBalance(current_user.wallet), 'ether')

    state = {
        'total_users':list(tot_data.username),
        'total_wallets':len(tot_data),
        'total_points':total_points,
        'my_points':my_points
    }

    print(state)
    
    return render_template('home/transaction.html', segment='index', state=state)



@blueprint.route('/settings', methods=['GET', 'POST'])
@login_required
def settings():
    print(current_user.username)
#     print(login_user(user))
    if request.method == 'POST':
        print(request.form.to_dict())
        
        update_date = request.form.to_dict()
        
        conn = sqlite3.connect("/home/site/flask-volt-dashboard/apps/db.sqlite3")
        cur = conn.cursor()
        
        email_str = update_date['birthday'].split('/')
        
        update_qry = f"""
        UPDATE Users
        SET first_name='{update_date['first_name']}'
          , last_name='{update_date['last_name']}'
          , birthday='{email_str[2]+email_str[0]+email_str[1]}'
          , gender='{update_date['gender']}'
          , email='{update_date['email']}'
          , phone='{update_date['phone']}'
          
        WHERE username='{current_user.username}'
        """
        print(update_qry)
        cur.execute(update_qry)
        conn.commit()
        
    my_points =  Web3.fromWei(w3.eth.getBalance(current_user.wallet), 'ether')

    return render_template('home/settings.html', my_points=my_points, segment='index')



@blueprint.route('/trans_info', methods = ['GET','POST'])
@login_required
def trans_info():
    BOARD_CNT = 20
    num = request.args.get('num',1,type=int)
    print(num)
    num_list_l = [num,num+1,num+2,num+3,num+4]

    
#     web3 = Web3(Web3.HTTPProvider(BLOCKCHAIN_ADR))
    total_block_num  = w3.eth.blockNumber
    
    if num > total_block_num / BOARD_CNT:
        num =int(total_block_num / BOARD_CNT)-1
    print(num)
    block_height_l = []  
    block_hash_l   = [] 
    timestamp_l    = []
    difficulty_l   = []
#     miner_l        = []
#     gas_used_l     = []
    N_transaction_l= []
#     nonce_l       = []
    
    for i in range(BOARD_CNT):
        print("/"*20,w3.eth.blockNumber-i-(BOARD_CNT*(num-1)))
        block_n = w3.eth.blockNumber-i-(BOARD_CNT*(num-1))
        print(datetime.datetime.fromtimestamp(w3.eth.get_block(block_n)['timestamp']).strftime("%Y-%m-%d %H:%M:%S"))
        block_height_l .append(block_n)
        block_hash_l   .append(w3.eth.get_block(block_n)['hash'].hex())
        timestamp_l    .append(datetime.datetime.fromtimestamp(w3.eth.get_block(block_n)['timestamp']).strftime("%Y-%m-%d %H:%M:%S"))
        difficulty_l   .append(w3.eth.get_block(block_n)['difficulty'])
        N_transaction_l.append(len(w3.eth.get_block(block_n)['transactions']))
            
        

    df_transaction = pd.DataFrame()
    df_transaction['block_height']  = block_height_l  
    df_transaction['block_hash']  = block_hash_l   
    df_transaction['timestamp']  = timestamp_l    
    df_transaction['difficulty']  = difficulty_l   
#     df_transaction['miner']  = miner_l        
#     df_transaction['gas_used']  = gas_used_l    
    df_transaction['N_transaction']  = N_transaction_l
    
    return render_template('home/transaction_info.html', segment='index',
                           df_transaction=df_transaction, num= num, num_list_l = num_list_l)


@blueprint.route('/block_detail/<blk_height>', methods = ['GET','POST'])
@login_required
def block_detail(blk_height):
#     blk_height = request.args.get('blk_height', 1, type=int)
    print(blk_height)
    blk_height = int(blk_height)
    blk_info = w3.eth.get_block(blk_height)
    print(blk_info)
    
    trans = []
    for trans_id in blk_info['transactions']:
        trans_info = w3.eth.get_transaction(trans_id.hex())
        
        conn = sqlite3.connect("/home/site/flask-volt-dashboard/apps/db.sqlite3")
    
        from_user = pd.read_sql(f"SELECT username FROM Users WHERE wallet='{trans_info['from']}'",conn).username.values[0]
        
        to_user = pd.read_sql(f"SELECT username FROM Users WHERE wallet='{trans_info['to']}'",conn).username.values[0]
        
        trans.append({'from':from_user,
                      'to':to_user,
                      'value':Web3.fromWei(trans_info['value'], 'ether')})
    print(trans)
    
    
        
    return render_template('home/block_detail.html', segment='index', trans=trans)


@blueprint.route('/block_info', methods = ['GET','POST'])
@login_required
def block_info():
    BOARD_CNT = 20
    num = request.args.get('num',1,type=int)
    print(num)
    num_list_l = [num,num+1,num+2,num+3,num+4]

    
#     web3 = Web3(Web3.HTTPProvider(BLOCKCHAIN_ADR))
    total_block_num  = w3.eth.blockNumber
    
    if num > total_block_num / BOARD_CNT:
        num =int(total_block_num / BOARD_CNT)-1
    print(num)
    block_height_l = []  
    block_hash_l   = [] 
    timestamp_l    = []
    difficulty_l   = []
#     miner_l        = []
#     gas_used_l     = []
    N_transaction_l= []
#     nonce_l       = []
    
    for i in range(BOARD_CNT):
        print("/"*20,w3.eth.blockNumber-i-(BOARD_CNT*(num-1)))
        block_n = w3.eth.blockNumber-i-(BOARD_CNT*(num-1))
        print(datetime.datetime.fromtimestamp(w3.eth.get_block(block_n)['timestamp']).strftime("%Y-%m-%d %H:%M:%S"))
        block_height_l .append(block_n)
        block_hash_l   .append(w3.eth.get_block(block_n)['hash'].hex())
        timestamp_l    .append(datetime.datetime.fromtimestamp(w3.eth.get_block(block_n)['timestamp']).strftime("%Y-%m-%d %H:%M:%S"))
        difficulty_l   .append(w3.eth.get_block(block_n)['difficulty'])
#         miner_l        .append(w3.eth.get_block(w3.eth.blockNumber-i)['miner'])
#         gas_used_l     .append(w3.eth.get_block(w3.eth.blockNumber-i)['gasUsed'])
        N_transaction_l.append(len(w3.eth.get_block(block_n)['transactions']))
#         nonce_l        .append(w3.eth.get_block(w3.eth.blockNumber-i)['nonce'].hex())
    df_transaction = pd.DataFrame()
    df_transaction['block_height']  = block_height_l  
    df_transaction['block_hash']  = block_hash_l   
    df_transaction['timestamp']  = timestamp_l    
    df_transaction['difficulty']  = difficulty_l   
#     df_transaction['miner']  = miner_l        
#     df_transaction['gas_used']  = gas_used_l    
    df_transaction['N_transaction']  = N_transaction_l
#     df_transaction['nonce']  = nonce_l      

    return render_template('home/block_info.html',
                           df_transaction = df_transaction, num= num, num_list_l = num_list_l)


@blueprint.route('/index')
@login_required
def index():
    conn = sqlite3.connect("/home/site/flask-volt-dashboard/apps/db.sqlite3")
    cur = conn.cursor()

    tot_data = pd.read_sql(f"SELECT * FROM Users", conn)
    total_points = float(sum([Web3.fromWei(w3.eth.getBalance(i), 'ether') for i in w3.eth.accounts]))
    my_points =  Web3.fromWei(w3.eth.getBalance(current_user.wallet), 'ether')

    state = {
        'total_wallets':len(tot_data),
        'total_points':total_points,
        'my_points':my_points
    }
    
    print(state)

    return render_template('home/index.html', segment='index', state=state)




# @blueprint.route('/<template>')
# @login_required
# def route_template(template):

#     try:

#         if not template.endswith('.html'):
#             template += '.html'

#         # Detect the current page
#         segment = get_segment(request)

#         # Serve the file (if exists) from app/templates/home/FILE.html
#         return render_template("home/" + template, segment=segment)

#     except TemplateNotFound:
#         return render_template('home/page-404.html'), 404

#     except:
#         return render_template('home/page-500.html'), 500


# # Helper - Extract current page name from request
# def get_segment(request):

#     try:

#         segment = request.path.split('/')[-1]

#         if segment == '':
#             segment = 'index'

#         return segment

#     except:
#         return None
