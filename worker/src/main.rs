extern crate requests; // Used for talking to API
extern crate ssh2; // Used for connecting to DICE machines

use requests::ToJson;
use ssh2::Session;

mod collector { // Grabs data from DICE machines
    pub struct CollectorCredentials {
        pub username: String,
        pub password: String
    }
    pub struct TargetMachine {
        pub ip: String,
        pub port: u8
    }
    pub struct MachineInfo {
        pub in_use: bool
    }
    pub fn fetch_machine(target: TargetMachine, creds: CollectorCredentials) -> MachineInfo {
        panic!("Not implemented!");
    }
}
mod api { // Communicates with backend API
    let URL: &str = "https://mapp.betterinformatics.com/api";
    pub struct APICredentials {
        pub api_key: String
    }
    pub struct APISession {
        pub session_cookie: String
    }
    pub enum Status {
        Success,
        AuthFailure,
        ConnectionFailure,
        OtherFailure,
    }
    pub fn authenticate(creds: &APICredentials) -> APISession {
        APISession {
            session_cookie: "im_not_a_cookie".to_string(),
        }
    }
    impl APISession {
        pub fn get_task(&self) -> Vec<collector::MachineInfo> {
            panic!("Not implemented!");
        }
        pub fn push_machine(
            &self,
            machine_info: &collector::MachineInfo,
        ) -> Status {
            println!("Using session: {}", self.session_cookie);
            // TODO: implement
            Status::Success
        }
        pub fn push_machines(
            &self,
            machines: &[collector::MachineInfo],
        ) -> Status {
            for m in machines {
                let _ = self.push_machine(m);
            }
            Status::Success
        }
    }
}

fn main() {
    // Start by authenticating with the API and grabbing keys
    // Next we loop through our assigned DICE machines
    //     for each machine we should collect data from them
    //     we should store the results on disk (in an encrypted format)
    // We should then read from these results and forward them to the API
}
