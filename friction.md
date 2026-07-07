Q: Why is every TON transaction actually a message cascade?
A: Everything in TON is a message from one entity to another, and it's all asynchronous. Sending TON means sending a message to the receiver, and a transaction is one account's act of processing one incoming message. So the receiver processes my message in its own separate transaction, and in case of a bounce, sends a message back — which the sender processes in yet another transaction. One user action, several messages, and one transaction per message processed: a cascade.


### Day 1 


#### get_transactions(): 

aborted → did MY account's processing of this message fail?
credited → did the money stay with me?


### uninit (account status)

Address has a balance but NO code deployed yet — money parked at
coordinates where no program lives. On TON every wallet is a smart
contract, deployed lazily: the first OUTGOING send attaches the wallet
code and flips status to "active". Receive-only wallets (like mine)
stay uninit — and every incoming tx shows aborted, since there's no
code to run.


### Day 2



SPAM_BODY is in base64 
Standard text is usually stored in 8-bit bytes. 

Base64 gets its name because it takes that data and regroups it into 6-bit chunks.
Because $2^6 = 64$, a 6-bit chunk can represent exactly 64 different possible values (from 0 to 63).

The Base64 system has an index containing exactly 64 "safe" characters:Uppercase letters (A-Z)Lowercase letters (a-z)Numbers (0-9)Two symbols (+ and /)

It takes your raw data, slices it into 6-bit pieces, looks up each piece in that 64-character index, and spits out the corresponding text string.


Q: What is a reference and why do cells have them ?
A: A reference is a cell's pointer to a child cell (up to 4 per cell). They exist because a cell caps at 1023 bits — anything bigger must be split across children, and children's children, forming a tree. Since cells are identified by their hashes, identical subtrees get stored once and shared — so the structure is really a DAG with automatic deduplication.
