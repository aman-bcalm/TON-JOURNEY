import "@acton/io"
import "@acton/emulation/network"
import "@acton/emulation/scripts"

import "@contracts/types"
import "@wrappers/TokenVault.gen"

fun main() {
    val deployer = scripts.wallet("deployer");

    val contract = TokenVault.fromStorage({ balances: ([] as Balances), totalDeposits: 0 });
    val res = contract.deploy(deployer.address, { value: ton("0.05") });
    if (res.waitForFirstTransaction() == null) {
        return;
    }

    println("Deployed vault to {}", contract.address);
    println("Total deposits: {}", contract.getTotalDeposits());
}
