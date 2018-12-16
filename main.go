package main

import (
	"bytes"
	"crypto/sha512"
	"crypto/tls"
	"crypto/x509"
	"encoding/hex"
	"encoding/json"
	"io/ioutil"
	"net/http"
	"os"
	"os/exec"
	"os/signal"
	"regexp"
	"strings"
	"syscall"
	"time"

	"github.com/pkg/errors"
	"github.com/robfig/cron"
	log "github.com/sirupsen/logrus"
)

var letsencryptPem = `-----BEGIN CERTIFICATE-----
MIIFazCCA1OgAwIBAgIRAIIQz7DSQONZRGPgu2OCiwAwDQYJKoZIhvcNAQELBQAw
TzELMAkGA1UEBhMCVVMxKTAnBgNVBAoTIEludGVybmV0IFNlY3VyaXR5IFJlc2Vh
cmNoIEdyb3VwMRUwEwYDVQQDEwxJU1JHIFJvb3QgWDEwHhcNMTUwNjA0MTEwNDM4
WhcNMzUwNjA0MTEwNDM4WjBPMQswCQYDVQQGEwJVUzEpMCcGA1UEChMgSW50ZXJu
ZXQgU2VjdXJpdHkgUmVzZWFyY2ggR3JvdXAxFTATBgNVBAMTDElTUkcgUm9vdCBY
MTCCAiIwDQYJKoZIhvcNAQEBBQADggIPADCCAgoCggIBAK3oJHP0FDfzm54rVygc
h77ct984kIxuPOZXoHj3dcKi/vVqbvYATyjb3miGbESTtrFj/RQSa78f0uoxmyF+
0TM8ukj13Xnfs7j/EvEhmkvBioZxaUpmZmyPfjxwv60pIgbz5MDmgK7iS4+3mX6U
A5/TR5d8mUgjU+g4rk8Kb4Mu0UlXjIB0ttov0DiNewNwIRt18jA8+o+u3dpjq+sW
T8KOEUt+zwvo/7V3LvSye0rgTBIlDHCNAymg4VMk7BPZ7hm/ELNKjD+Jo2FR3qyH
B5T0Y3HsLuJvW5iB4YlcNHlsdu87kGJ55tukmi8mxdAQ4Q7e2RCOFvu396j3x+UC
B5iPNgiV5+I3lg02dZ77DnKxHZu8A/lJBdiB3QW0KtZB6awBdpUKD9jf1b0SHzUv
KBds0pjBqAlkd25HN7rOrFleaJ1/ctaJxQZBKT5ZPt0m9STJEadao0xAH0ahmbWn
OlFuhjuefXKnEgV4We0+UXgVCwOPjdAvBbI+e0ocS3MFEvzG6uBQE3xDk3SzynTn
jh8BCNAw1FtxNrQHusEwMFxIt4I7mKZ9YIqioymCzLq9gwQbooMDQaHWBfEbwrbw
qHyGO0aoSCqI3Haadr8faqU9GY/rOPNk3sgrDQoo//fb4hVC1CLQJ13hef4Y53CI
rU7m2Ys6xt0nUW7/vGT1M0NPAgMBAAGjQjBAMA4GA1UdDwEB/wQEAwIBBjAPBgNV
HRMBAf8EBTADAQH/MB0GA1UdDgQWBBR5tFnme7bl5AFzgAiIyBpY9umbbjANBgkq
hkiG9w0BAQsFAAOCAgEAVR9YqbyyqFDQDLHYGmkgJykIrGF1XIpu+ILlaS/V9lZL
ubhzEFnTIZd+50xx+7LSYK05qAvqFyFWhfFQDlnrzuBZ6brJFe+GnY+EgPbk6ZGQ
3BebYhtF8GaV0nxvwuo77x/Py9auJ/GpsMiu/X1+mvoiBOv/2X/qkSsisRcOj/KK
NFtY2PwByVS5uCbMiogziUwthDyC3+6WVwW6LLv3xLfHTjuCvjHIInNzktHCgKQ5
ORAzI4JMPJ+GslWYHb4phowim57iaztXOoJwTdwJx4nLCgdNbOhdjsnvzqvHu7Ur
TkXWStAmzOVyyghqpZXjFaH3pO3JLF+l+/+sKAIuvtd7u+Nxe5AW0wdeRlN8NwdC
jNPElpzVmbUq4JUagEiuTDkHzsxHpFKVK7q4+63SM1N95R1NbdWhscdCb+ZAJzVc
oyi3B43njTOQ5yOf+1CceWxG1bQVs5ZufpsMljq4Ui0/1lvh+wjChP4kqKOJ2qxq
4RgqsahDYVvTH9w7jXbyLeiNdd8XM2w9U/t7y0Ff/9yi0GE44Za4rF2LN9d11TPA
mRGunUHBcnWEvgJBQl9nJEiU0Zsnvgc/ubhPgXRR4Xq37Z0j4r7g1SgEEzwxA57d
emyPxgcYxn/eR44/KJ4EBs+lVDR3veyJm+kXQ99b21/+jh5Xos1AnX5iItreGCc=
-----END CERTIFICATE-----
-----BEGIN CERTIFICATE-----
MIIEkjCCA3qgAwIBAgIQCgFBQgAAAVOFc2oLheynCDANBgkqhkiG9w0BAQsFADA/
MSQwIgYDVQQKExtEaWdpdGFsIFNpZ25hdHVyZSBUcnVzdCBDby4xFzAVBgNVBAMT
DkRTVCBSb290IENBIFgzMB4XDTE2MDMxNzE2NDA0NloXDTIxMDMxNzE2NDA0Nlow
SjELMAkGA1UEBhMCVVMxFjAUBgNVBAoTDUxldCdzIEVuY3J5cHQxIzAhBgNVBAMT
GkxldCdzIEVuY3J5cHQgQXV0aG9yaXR5IFgzMIIBIjANBgkqhkiG9w0BAQEFAAOC
AQ8AMIIBCgKCAQEAnNMM8FrlLke3cl03g7NoYzDq1zUmGSXhvb418XCSL7e4S0EF
q6meNQhY7LEqxGiHC6PjdeTm86dicbp5gWAf15Gan/PQeGdxyGkOlZHP/uaZ6WA8
SMx+yk13EiSdRxta67nsHjcAHJyse6cF6s5K671B5TaYucv9bTyWaN8jKkKQDIZ0
Z8h/pZq4UmEUEz9l6YKHy9v6Dlb2honzhT+Xhq+w3Brvaw2VFn3EK6BlspkENnWA
a6xK8xuQSXgvopZPKiAlKQTGdMDQMc2PMTiVFrqoM7hD8bEfwzB/onkxEz0tNvjj
/PIzark5McWvxI0NHWQWM6r6hCm21AvA2H3DkwIDAQABo4IBfTCCAXkwEgYDVR0T
AQH/BAgwBgEB/wIBADAOBgNVHQ8BAf8EBAMCAYYwfwYIKwYBBQUHAQEEczBxMDIG
CCsGAQUFBzABhiZodHRwOi8vaXNyZy50cnVzdGlkLm9jc3AuaWRlbnRydXN0LmNv
bTA7BggrBgEFBQcwAoYvaHR0cDovL2FwcHMuaWRlbnRydXN0LmNvbS9yb290cy9k
c3Ryb290Y2F4My5wN2MwHwYDVR0jBBgwFoAUxKexpHsscfrb4UuQdf/EFWCFiRAw
VAYDVR0gBE0wSzAIBgZngQwBAgEwPwYLKwYBBAGC3xMBAQEwMDAuBggrBgEFBQcC
ARYiaHR0cDovL2Nwcy5yb290LXgxLmxldHNlbmNyeXB0Lm9yZzA8BgNVHR8ENTAz
MDGgL6AthitodHRwOi8vY3JsLmlkZW50cnVzdC5jb20vRFNUUk9PVENBWDNDUkwu
Y3JsMB0GA1UdDgQWBBSoSmpjBH3duubRObemRWXv86jsoTANBgkqhkiG9w0BAQsF
AAOCAQEA3TPXEfNjWDjdGBX7CVW+dla5cEilaUcne8IkCJLxWh9KEik3JHRRHGJo
uM2VcGfl96S8TihRzZvoroed6ti6WqEBmtzw3Wodatg+VyOeph4EYpr/1wXKtx8/
wApIvJSwtmVi4MFU5aMqrSDE6ea73Mj2tcMyo5jMd6jmeWUHK8so/joWUoHOUgwu
X4Po1QYz+3dszkDqMp4fklxBwXRsW10KXzPMTZ+sOPAveyxindmjkW8lGy+QsRlG
PfZ+G6Z6h7mjem0Y+iWlkYcV4PIWL1iwBi8saCbGS5jN2p8M+X+Q7UNKEkROb3N6
KOqkqm57TH2H3eDJAkSnh6/DNFu0Qg==
-----END CERTIFICATE-----`

var cachedMachineList []byte

func getBase() string {
	if os.Getenv("DEBUG") == "true" {
		return "https://mapp-dev.betterinformatics.com"
	}
	return "https://mapp.betterinformatics.com"
}

func getMachines() (machines []string, err error) {
	var listStruct struct{ Machines []string }
	var listBytes []byte

	machineListPath := os.Getenv("MACHINE_LIST")
	if machineListPath == "" {
		log.Infoln("Could not find machine list. Downloading and using machine list...")

		client, err := getHTTPClient()
		if err != nil {
			return nil, errors.Wrap(err, "could not get http client")
		}

		resp, err := client.Get(getBase() + "/api/rooms/all")
		if err != nil {
			return nil, errors.Wrap(err, "could not download machines list")
		}

		listBytes, err = ioutil.ReadAll(resp.Body)
		if err != nil {
			return nil, errors.Wrap(err, "could not read API response for machines list")
		}

		defer resp.Body.Close()
	} else {
		if cachedMachineList == nil {
			listBytes, err = ioutil.ReadFile(machineListPath)
			if err != nil {
				return nil, errors.Wrap(err, "could not open machines file")
			}
			cachedMachineList = listBytes
		} else {
			listBytes = cachedMachineList
		}
	}

	if err := json.Unmarshal(listBytes, &listStruct); err != nil {
		return nil, errors.Wrap(err, "could not read machines file json contents")
	}

	machines = listStruct.Machines
	return
}

func checkAuthentication() error {
	_, err := exec.Command(
		"ssh",
		"-o", "ForwardX11=no",
		"-o", "GSSAPIAuthentication=yes",
		"-o", "GSSAPIDelegateCredentials=no",
		"-o", "BatchMode=yes",
		"student.login.inf.ed.ac.uk",
		"exit",
	).Output()

	if err != nil {
		return err
	}

	return nil
}

type MachineResult struct {
	Hostname  string `json:"hostname"`
	User      string `json:"user"`
	Timestamp string `json:"timestamp"`
	Status    string `json:"status"`
	Error     error  `json:"-"`
}

var reo = regexp.MustCompile(`^\s+(\w+)\s+\d+\s+(\w+)\s+seat0\s+$`)

func searchWorker(id int, jobs <-chan string, results chan<- MachineResult) {
	for machine := range jobs {
		// fmt.Println("worker", id, "started job", machine)

		location, _ := time.LoadLocation("Europe/London")

		result := MachineResult{
			Hostname:  machine,
			Timestamp: time.Now().In(location).Format(time.RFC3339),
		}

		cmd := exec.Command(
			"ssh",
			"-o", "ForwardX11=no",
			"-o", "GSSAPIAuthentication=yes",
			"-o", "GSSAPIDelegateCredentials=no",
			"-o", "BatchMode=yes",
			"-o", "ServerAliveInterval=5",
			"-o", "ServerAliveCountMax=3",
			"-o", "ConnectTimeout=5s",
			"-o", "StrictHostKeyChecking=no",
			machine+".inf.ed.ac.uk",
			"/usr/bin/printf '%s' $(PIDS=$(pidof lightdm); for pid in $PIDS; do ps -ho user --ppid $pid | fgrep -v -e 'root'; done)",
		)

		var errbuf bytes.Buffer
		cmd.Stderr = &errbuf

		out, err := cmd.Output()

		if err != nil {
			result.Status = "offline"
			result.Error = errors.Wrap(err, errbuf.String())

			if strings.Contains(errbuf.String(), "Name or service not known") {
				result.Status = "unknown"
			}
		} else {
			result.Status = "online"
			result.User = strings.TrimSpace(string(out))
			if result.User == "lightdm" {
				result.User = ""
			}
		}

		results <- result
		// fmt.Println("worker", id, "finished job", result)
	}
}

func getHTTPClient() (*http.Client, error) {
	pool := x509.NewCertPool()
	if pool.AppendCertsFromPEM([]byte(letsencryptPem)) != true {
		return nil, errors.New("failed to append cert to pool")
	}

	tlsConf := &tls.Config{RootCAs: pool}
	tlsConf.BuildNameToCertificate()

	client := &http.Client{Transport: &http.Transport{
		TLSClientConfig: tlsConf,
	}}
	return client, nil
}

func sendUpdate(payload interface{}) error {
	data, err := json.Marshal(payload)
	if err != nil {
		return err
	}

	client, err := getHTTPClient()
	if err != nil {
		return errors.Wrap(err, "could not get http client")
	}

	_, err = client.Post(
		getBase()+"/api/update",
		"application/json",
		bytes.NewBuffer(data),
	)
	return err
}

func performSearch(machines []string, secret, callbackKey string) {
	start := time.Now()
	count := len(machines)

	jobs := make(chan string, count)
	resultsChan := make(chan MachineResult, count)

	workers := 100
	if count < workers {
		workers = count
	}

	for w := 0; w < workers; w++ {
		go searchWorker(w, jobs, resultsChan)
	}

	for _, machine := range machines {
		jobs <- machine
	}

	log.Println("JOBS SENT")
	close(jobs)

	var payload struct {
		Machines    []MachineResult `json:"machines"`
		CallbackKey string          `json:"callback-key"`
	}

	payload.Machines = make([]MachineResult, count)
	payload.CallbackKey = callbackKey

	hash := sha512.New()

	for i := 0; i < count; i++ {
		result := <-resultsChan

		if result.Error != nil {
			log.
				WithField("host", result.Hostname).
				WithField("status", result.Status).
				WithField("error", result.Error).
				Errorln("NO-GO")
		} else if result.User != "" {
			hash.Reset()
			if _, err := hash.Write([]byte(result.User + secret)); err != nil {
				log.WithField("error", err).Errorln("could not hash user")
				result.User = ""
			} else {
				result.User = hex.EncodeToString(hash.Sum(nil))
				log.
					WithField("status", result.Status).
					WithField("host", result.Hostname).
					WithField("user", result.User[:15]+"...").
					Infoln("SUCCESS WITH USER")
			}
		} else {
			log.
				WithField("status", result.Status).
				WithField("host", result.Hostname).
				Infoln("SUCCESS")
		}

		result.Error = nil
		payload.Machines[i] = result
	}

	log.WithField("servers", count).WithField("timestamp", time.Now()).Printf("DONE ITERATION")

	if err := sendUpdate(payload); err != nil {
		log.WithField("error", err).Errorln("ERROR could not reach callback")
	} else {
		duration := time.Now().Sub(start)
		log.WithField("duration", duration).Infoln("CALLBACK ok for all machines")
	}

	// Massive payload. Lets not show it.
	// Payload also shows callback key..
	// log.Printf("RESULTS %+v\n", payload)
}

func main() {
	machines, err := getMachines()
	if err != nil {
		log.WithField("error", err).Fatalln("could not get machines")
		return
	}

	callbackKey := os.Getenv("CALLBACK_KEY")
	secret := os.Getenv("MAPP_SECRET")
	if callbackKey == "" || secret == "" {
		log.Fatalln("missing CALLBACK_KEY or MAPP_SECRET")
		return
	}

	log.Info("CHECKING authentication...")

	err = checkAuthentication()
	if err != nil {
		log.WithField("error", err).Fatalln("AUTH FAIL!")
		return
	}

	log.Info("AUTH OK, starting initial run...")

	performSearch(machines, secret, callbackKey)

	cronSearch := func(msg string) func() {
		return func() {
			if newMachines, err := getMachines(); err != nil {
				log.WithField("error", err).Fatalln("could not get machines")
			} else {
				machines = newMachines
			}

			log.WithField("msg", msg).Println("CRON TRIGGERED")
			performSearch(machines, secret, callbackKey)
		}
	}

	c := cron.New()

	// weekdays, between 9am and 6pm,
	// at 8, 15, 45, 52 past the hour
	// See https://crontab.guru/ (remove first number [seconds])
	c.AddFunc("0 8,15,45,52 09-18 * * 1-5", cronSearch("near the hour, from 9am to 6pm, weekly"))

	// Always do it on the hour and at the half hour.
	c.AddFunc("0 0,30 * * * *", cronSearch("every thirty minutes"))

	// Test
	// c.AddFunc("0 */1 * * * *", cronSearch("every minute"))

	log.Println("CRON LOADED.")

	c.Start()

	// Create new signal receiver
	sc := make(chan os.Signal, 1)
	signal.Notify(sc, syscall.SIGINT, syscall.SIGTERM, os.Interrupt, os.Kill)

	<-sc

	log.Println("Shutting down...")

	c.Stop()

}
