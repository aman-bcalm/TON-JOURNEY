enum Errors {
    InsufficientBalance = 0x1001
    InvalidMessage = 0xFFFF
}

type Balances = map<address, coins>

struct Storage {
    balances: Balances = []
    totalDeposits: coins
}

fun Storage.load(): Storage {
    return Storage.fromCell(contract.getData());
}

fun Storage.save(self) {
    contract.setData(self.toCell());
}

struct (0x1cf5f859) Deposit {}

struct (0x5fcc3d14) Withdraw {
    amount: coins
}

struct (0x8a219b02) WithdrawOk {
    amount: coins
}
