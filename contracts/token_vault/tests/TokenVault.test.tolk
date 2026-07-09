import "@stdlib/gas-payments"
import "@acton/emulation/network"
import "@acton/emulation/testing"
import "@acton/testing/expect"
import "@acton/types/big_array"
import "@contracts/types"
import "@wrappers/TokenVault.gen"

get fun `test deposit updates balance`() {
    val (contract, deployer, _) = setupTest();

    val res = contract.sendDeposit(deployer.address, { value: ton("2") });
    expect(res).toHaveSuccessfulTx<Deposit>({
        from: deployer.address,
        to: contract.address,
    });

    expect(contract.getBalance(deployer.address)).toEqual(ton("2") as int);
    expect(contract.getTotalDeposits()).toEqual(ton("2") as int);
}

get fun `test deposit tracks each depositor separately`() {
    val (contract, deployer, notDeployer) = setupTest();

    contract.sendDeposit(deployer.address, { value: ton("2") });
    contract.sendDeposit(notDeployer.address, { value: ton("3") });

    expect(contract.getBalance(deployer.address)).toEqual(ton("2") as int);
    expect(contract.getBalance(notDeployer.address)).toEqual(ton("3") as int);
    expect(contract.getTotalDeposits()).toEqual(ton("5") as int);
}

get fun `test partial withdraw leaves remainder`() {
    val (contract, deployer, _) = setupTest();

    contract.sendDeposit(deployer.address, { value: ton("2") });

    val res = contract.sendWithdraw(deployer.address, ton("0.5"), { value: ton("0.05") });
    expect(res).toHaveSuccessfulTx<Withdraw>({
        from: deployer.address,
        to: contract.address,
    });

    expect(contract.getBalance(deployer.address)).toEqual(ton("1.5") as int);
    expect(contract.getTotalDeposits()).toEqual(ton("1.5") as int);
}

get fun `test withdraw more than balance fails`() {
    val (contract, deployer, _) = setupTest();

    contract.sendDeposit(deployer.address, { value: ton("1") });

    val res = contract.sendWithdraw(deployer.address, ton("5"), { value: ton("0.05") });
    expect(res).toHaveFailedTx({
        from: deployer.address,
        to: contract.address,
        exitCode: Errors.InsufficientBalance,
    });

    expect(contract.getBalance(deployer.address)).toEqual(ton("1") as int);
    expect(contract.getTotalDeposits()).toEqual(ton("1") as int);
}

get fun `test withdraw with no deposit fails`() {
    val (contract, _, notDeployer) = setupTest();

    val res = contract.sendWithdraw(notDeployer.address, ton("0.1"), { value: ton("0.05") });
    expect(res).toHaveFailedTx({
        from: notDeployer.address,
        to: contract.address,
        exitCode: Errors.InsufficientBalance,
    });
}

get fun `test bounced withdrawal restores balance`() {
    val (contract, deployer, _) = setupTest();

    contract.sendDeposit(deployer.address, { value: ton("2") });

    val res = contract.sendWithdraw(deployer.address, ton("1"), { value: ton("0.05") });
    expect(res).toHaveSuccessfulTx<Withdraw>({
        from: deployer.address,
        to: contract.address,
    });
    expect(contract.getBalance(deployer.address)).toEqual(ton("1") as int);

    // Simulate the withdrawal transfer failing to reach the depositor: the network
    // returns the value with a bounced body (0xFFFFFFFF prefix + original WithdrawOk).
    val bouncedMsg = createMessage({
        bounce: false,
        value: ton("1"),
        dest: contract.address,
        body: beginCell()
            .storeUint(0xFFFFFFFF, 32)
            .storeSlice(WithdrawOk { amount: ton("1") }.toCell().beginParse())
            .endCell(),
    }).bounced();

    val bounceRes = testing.processSingleTraceStep(deployer.address, bouncedMsg);
    expect(BigArray<SendResult>.createFromArray([bounceRes])).toHaveSuccessfulTx({
        from: deployer.address,
        to: contract.address,
    });

    expect(contract.getBalance(deployer.address)).toEqual(ton("2") as int);
    expect(contract.getTotalDeposits()).toEqual(ton("2") as int);
}

fun setupTest(): (TokenVault, Treasury, Treasury) {
    val deployer = testing.treasury("deployer");
    val notDeployer = testing.treasury("notDeployer");

    val contract = TokenVault.fromStorage({ balances: ([] as Balances), totalDeposits: 0 });
    val res = contract.deploy(deployer.address, { value: ton("1") });
    expect(res).toHaveSuccessfulDeploy({ to: contract.address });

    return (contract, deployer, notDeployer);
}
