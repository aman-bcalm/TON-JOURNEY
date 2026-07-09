import "types"

contract TokenVault {
    author: "Aman"
    version: "1.0.0"
    description: "Vault tracking per-address deposit balances with capped withdrawals"
    storage: Storage
    incomingMessages: AllowedMessage
}

type AllowedMessage =
    | Deposit
    | Withdraw

fun onInternalMessage(in: InMessage) {
    val msg = lazy AllowedMessage.fromSlice(in.body);

    match (msg) {
        Deposit => {
            var storage = lazy Storage.load();

            val current = storage.balances.get(in.senderAddress);
            val existing = current.isFound ? current.loadValue() : 0 as coins;
            storage.balances.set(in.senderAddress, existing + in.valueCoins);
            storage.totalDeposits += in.valueCoins;
            storage.save();
        }
        Withdraw => {
            var storage = lazy Storage.load();

            val current = storage.balances.get(in.senderAddress);
            val balance = current.isFound ? current.loadValue() : 0 as coins;
            assert (msg.amount <= balance) throw Errors.InsufficientBalance;

            storage.balances.set(in.senderAddress, balance - msg.amount);
            storage.totalDeposits -= msg.amount;
            storage.save();

            val reply = createMessage({
                bounce: BounceMode.Only256BitsOfBody,
                dest: in.senderAddress,
                value: msg.amount,
                body: WithdrawOk { amount: msg.amount },
            });
            reply.send(SEND_MODE_PAY_FEES_SEPARATELY);
        }
        else => {
            assert (in.body.isEmpty()) throw Errors.InvalidMessage;
        }
    }
}

fun onBouncedMessage(in: InMessageBounced) {
    in.bouncedBody.skipBouncedPrefix();
    val msg = lazy WithdrawOk.fromSlice(in.bouncedBody);

    var storage = lazy Storage.load();

    val current = storage.balances.get(in.senderAddress);
    val existing = current.isFound ? current.loadValue() : 0 as coins;
    storage.balances.set(in.senderAddress, existing + msg.amount);
    storage.totalDeposits += msg.amount;
    storage.save();
}

get fun getBalance(addr: address): int {
    val storage = lazy Storage.load();

    val r = storage.balances.get(addr);
    return r.isFound ? r.loadValue() : 0;
}

get fun getTotalDeposits(): int {
    val storage = lazy Storage.load();

    return storage.totalDeposits;
}
