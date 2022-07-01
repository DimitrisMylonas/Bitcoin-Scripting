from bitcoinutils.setup import setup
from bitcoinutils.keys import P2shAddress, PrivateKey, PublicKey
from bitcoinutils.script import Script
import binascii
import click
import sys
from bitcoinutils.transactions import Transaction, TxInput, TxOutput, Sequence

#pubk1 = 4747e8746cddb33b0f7f95a90f89f89fb387cbb6
#pubk2 = 7fda9cf020c16cacf529c87d8de89bfc70b8c9cb
#pubk3 = 5dedfbf9ea599dd4e3ca6a80b333c472fd0b3f69

@click.command()
@click.option("--pubk1", help="Public key 1")
@click.option("--pubk2", help="Public key 2")
@click.option("--pubk3", help="Public key 3")

def main(pubk1, pubk2, pubk3):

    setup('regtest')

    if pubk1 and pubk2 and pubk3:
        print("\n\n First public key:", pubk1)
        print("\n Second public key:", pubk2)
        print("\n Third public key:", pubk3)
    else:
        print("ERROR: You have to set 3 public keys")
        sys.exit(1)
    #creating the redeem script to which the funds will be locked in
    redeem_script = Script(['OP_2', pubk1, pubk2, pubk3, 'OP_3', 'OP_CHECKMULTISIG'])
    P2SH_ADDRESS = P2shAddress.from_script(redeem_script)
    print("\n The P2SH address to send the funds is: ",P2SH_ADDRESS.to_string())

if __name__ == "__main__":
    main()