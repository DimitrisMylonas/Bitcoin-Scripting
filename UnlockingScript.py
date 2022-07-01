from bitcoinutils.transactions import Transaction, TxInput, TxOutput, Sequence, Locktime
from bitcoinutils.keys import P2pkhAddress, P2shAddress, PrivateKey, PublicKey
from bitcoinutils.setup import setup
from bitcoinutils.proxy import NodeProxy
from bitcoinutils.script import Script
import requests
import sys
from bitcoinutils.utils import to_satoshis
import click

#pub = 5dedfbf9ea599dd4e3ca6a80b333c472fd0b3f69
#priv1 = cMahea7zqjxrtgAbB7LSGbcQUr1uX1ojuat9jZodMN87Lc8ycuM4
#priv2 = cMahea7zqjxrtgAbB7LSGbcQUr1uX1ojuat9jZodMN87M73ZA41f
#p2sh = 2MyuGRcXVttYzjEjSAZpPzHbGwT2rd9zqyN
#p2pkh = mg5fdnuRygf6AmzsyTY2RzF7qnttjsAYPa

@click.command()
@click.option("--pub", help="The (3rd) public key needed to create the redeem script")
@click.option("--priv1", help="First private key for the P2PKH part")
@click.option("--priv2", help="Second private key for the P2PKH part")
@click.option("--p2sh", help="The P2SH address to get the funds from")
@click.option("--p2pkh", help="The P2PKH address to send the funds to")
@click.option("--user", help="proxy username")
@click.option("--password", help="proxy password")

def main(pub, priv1, priv2, p2sh, p2pkh, user, password):

    setup('regtest')

    if not user or not password:
        print("ERROR: You have to provide RPC user and password using the --user and --password options.")
        sys.exit(1)
    proxy = NodeProxy(user, password).get_proxy()

    if priv1 and priv2:
        #getting the two out of three public keys which will be used for creating the redeem script
        private_1 = PrivateKey(priv1)
        pubk1 = private_1.get_public_key().to_hex()
        private_2 = PrivateKey(priv2)
        pubk2 = private_2.get_public_key().to_hex()
    else:
        print("You have to provide 2 private keys! Use the --priv1 and --priv2 options.")
        sys.exit(1)

    if pub:
        #getting the third public key whicl will be used for creating the redeem script
        pubk3 = pub
    else:
        print("You have to provide a public key! Use the --pub option.")
        sys.exit(1)  

    if p2sh:
        #funds have been locked in this address
        P2SH_ADDRESS = p2sh 
    else:
        print("You have to provide a P2SH address! Use the --p2sh option.")
        sys.exit(1)

    if p2pkh:
        #funds will be sent to this address
        to_addr = P2pkhAddress(p2pkh)
    else:
        print("You have to provide a P2PKH address! Use the --p2pkh option.")
        sys.exit(1)

    proxy.importaddress(P2SH_ADDRESS , "P2SH", True)
    unspent = proxy.listunspent(0, 10000000, [P2SH_ADDRESS]) #all UTXOs for this address

    amount = 0
    list_of_txins = []
    #create the inputs of all UTXOs
    for i in unspent:
        txin = TxInput(i['txid'], i['vout'])
        list_of_txins.append(txin)
        #total amount of inputs' bitcoins
        amount = amount + to_satoshis(i['amount'])
    
    if amount == 0:
        print("There are no funds to move")
        sys.exit(0)
    
    print("Total amount of funds to move: ", amount, '(satoshis)')

    #recreating the redeem script as we did in the Locking Script 
    redeem_script = Script(['OP_2', pubk1, pubk2, pubk3, 'OP_3', 'OP_CHECKMULTISIG'])
    
    #calculating fees and tx size according to:
    #https://bitcoin.stackexchange.com/questions/1195/how-to-calculate-transaction-size-before-sending-legacy-non-segwit-p2pkh-p2sh
    feePerKb = 60000
    tx_size = len(list_of_txins) + len(list_of_txins) * 180 + 34 + 10 
    fees = to_satoshis(feePerKb*tx_size / (1024 * 10**8))
    print('fees:', fees, "(satoshis)")

    txout = TxOutput(amount - fees, to_addr.to_script_pub_key() )

    tx = Transaction(list_of_txins, [txout])
    
    #use the two private keys to sign each txin
    for i, txin in enumerate(list_of_txins):
        sig1 = private_1.sign_input(tx, i, redeem_script)
        sig2 = private_2.sign_input(tx, i, redeem_script) 
        #The 0 at the beginning of the script is because of a bug 
        #in CHECKMULTISIG that pops an extra value from the stack
        txin.script_sig = Script(["OP_0", sig1, sig2, redeem_script.to_hex()])

    signed_tx = tx.serialize()
    
    res = proxy.testmempoolaccept([signed_tx])
    if not res[0]['allowed']:
        print("Invalid transaction!")
        sys.exit(1)
    else:
        print("Transaction is valid!")

    print("\nRaw unsigned transaction:\n" + tx.serialize())
    print("\nRaw signed transaction:\n" + signed_tx)
    print("\nTxId:", tx.get_txid())
    print("\nSending transaction...\n")
    proxy.sendrawtransaction(signed_tx)

if __name__ == "__main__":
    main()