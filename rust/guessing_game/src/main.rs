use rand::Rng;
use std::cmp::Ordering;
use std::io;

fn main() {
    let result = rand::thread_rng().gen_range(1, 101);

    println!("Hadaj cislo! Zadaj cislo:");
    let mut guess = String::new();
    io::stdin().read_line(&mut guess).expect("Nepodarilo sa precitat");
    let guess: u32 = guess.trim().parse().expect("Chcem cislo!");

    // Why reference?
    match guess.cmp(&result) {
        Ordering::Less => println!("Think bigger!"),
        Ordering::Greater => println!("You too bullish!"),
        Ordering::Equal => println!("JACKPOT PANKO!"),
    }


    // println!("Hadal si {} ale bolo {}", guess, result);
}
