# cemu-net-action

Run networked TI-84 Plus CE tests on GitHub Actions.

The action builds the CEmu autotester from [CEmu-lwIP-CE](https://github.com/alessiodam/CEmu-lwIP-CE), which emulates a USB CDC-ECM Ethernet adapter, and bridges that adapter to a TAP interface on the runner with NAT to the internet. A built-in DHCP server hands the calculator its address, so lwIP-CE's `lwip_network_up()` works with no extra setup.

## Usage

Plug the adapter in from your autotest sequence **after** files are transferred (file transfers use the USB port and unplug it):

```json
{
  "transfer_files": ["clibs.8xg", "LWIP.0.8xv", "...", "lwIPINST.8xp", "lwip.8xv", "lwIPCERT.8xv", "MYTEST.8xp"],
  "target": { "name": "MYTEST", "isASM": false },
  "sequence": [
    "delay|5000", "key|clear",
    "action|launch:INSTALL", "delay|30000", "key|left", "key|enter", "delay|5000", "key|clear",
    "usb|eth,cemu0,dhcp=192.168.84.2/24,gw=192.168.84.1,dns=1.1.1.1",
    "action|launch",
    "hashWait|1"
  ],
  "hashes": { "1": { "description": "done", "start": "vram_start", "size": "vram_16_size", "expected_CRCs": ["..."], "timeout": 600000 } }
}
```

```yaml
- uses: alessiodam/cemu-net-action@v1
  with:
    rom: ce.rom
    autotest: tests/autotest.json
    truststore: true
```

The `usb` step above matches the default inputs. It is also available as the `usb-step` output, and the truststore path as the `truststore` output, so you can call the action once without `autotest` to set things up, generate your JSON, then run `${{ steps.cemu.outputs.autotester }} your.json` yourself (for example to `saveVar` a log and parse it afterwards).

The ROM is not provided; fetch it from your own secret storage and pass its path.

## Inputs

| Input | Default | Description |
| --- | --- | --- |
| `autotest` | | Autotester JSON to run. Empty only sets things up. |
| `rom` | | CE ROM path, exported as `AUTOTESTER_ROM`. |
| `screenshots` | `false` | Dump a screenshot at every hash check (`-s`). |
| `truststore` | `false` | Download the signed lwIP-CE truststore `lwIPCERT.8xv`. |
| `cemu-repository` | `alessiodam/CEmu-lwIP-CE` | CEmu source to build. |
| `cemu-ref` | `master` | Branch, tag or commit to build. The build is cached per commit. |
| `tap` | `cemu0` | TAP interface name. |
| `host-address` | `192.168.84.1/24` | Runner address on the TAP, used as the calculator's gateway. |
| `calc-address` | `192.168.84.2` | Address leased to the calculator. |
| `dns` | `1.1.1.1` | DNS server handed to the calculator. |

## Outputs

| Output | Description |
| --- | --- |
| `autotester` | Path to the autotester binary. |
| `usb-step` | Sequence step that plugs the adapter in with the configured addresses. |
| `truststore` | Path to `lwIPCERT.8xv` when `truststore` is `true`. |

Linux runners only (`ubuntu-*`).
