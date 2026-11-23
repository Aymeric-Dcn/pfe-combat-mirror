# Force plate acquisition firmware (NUCLEO-F072RB)

Samples the 4 FlexiForce channels of the conditioning board and streams them to the PC through the ST-LINK USB cable. Register-level code (CMSIS only, no HAL).

**Origin:** this STM32CubeIDE project is a copy of my STM32 tutorials project, [stm32f072-baremetal-tutorials](https://github.com/Aymeric-Dcn/stm32f072-baremetal-tutorials) (after Laurent Latorre's tutorials on pomad.fr), taken at tag `3.5-adc-dma` (multi-channel ADC with DMA). The 48 MHz clock configuration, the BSP structure and the other drivers are unchanged. What changed:

| File | Change |
|---|---|
| `bsp/src/bsp.c` | `BSP_ADC_Init()`: 6 channels, triggered by TIM3, calibration, DMA half/complete interrupts. New `BSP_TIMER_Trigger_Init()` (TIM3, 2 kHz). `BSP_Console_Init()`: 921600 bauds, TX by DMA (channel 4) + `BSP_Console_SendDMA()`. `BSP_NVIC_Init()`: DMA1 channel 1 and TIM6. Timebase at 500 ms. |
| `app/src/frame.c` | New: conversion to millivolts and frame queue. |
| `app/src/stm32f0xx_it.c` | DMA1 channel 1 handler (one frame per scan, scan check and resync), TIM6 handler kept. |
| `app/src/main.c` | Initialisation and main loop. |

## Channels

| Signal | Nucleo pin | MCU | ADC channel |
|---|---|---|---|
| Sensor 1 | A0 | PA0 | IN0 |
| Sensor 2 | A1 | PA1 | IN1 |
| Sensor 3 | A2 | PA4 | IN4 |
| Sensor 4 | A3 | PB0 | IN8 |
| V_REF (mode) | A4 | PC1 | IN11 |
| Internal reference (VDDA) | — | — | IN17 |

- 2 kHz per channel: TIM3 triggers one ADC scan of the 6 channels, DMA stores it, the DMA interrupt converts it to millivolts (VDDA measured with the internal reference) and queues a frame. The main loop sends the queue by DMA.
- Serial link: ST-LINK virtual COM port (USART2, PA2/PA3), **921600 baud**, 8N1.
- The green LED (LD2) toggles every 0.5 s.
- TIM1 and PA8 are left free for the camera trigger.
- Scan check: if the ADC reports an overrun, or if the last slot of a scan does not hold the internal reference, the scan is dropped and the ADC and DMA restart at the start of the buffer (`BSP_ADC_Resync()`). The dropped scan appears as a gap on the PC. Without this check, an out-of-order buffer stayed shifted until a reset (seen on 23/11: channels A0 and A4 read swapped).

## Frame format

17 bytes, little endian, one frame per sample (34 kB/s):

| Bytes | Content |
|---|---|
| 0–1 | sync `0xA5 0x5A` |
| 2–3 | sample counter (uint16, wraps every 32.8 s) |
| 4–11 | sensors 1 to 4, mV (uint16) |
| 12–13 | V_REF, mV |
| 14–15 | VDDA, mV |
| 16 | checksum: sum of bytes 2 to 15, mod 256 |

A jump in the counter means lost frames. The PC script (`scripts/forceplate`) reads this format.

## Build and flash

In STM32CubeIDE: **File → Import → General → Existing Projects into Workspace**, select this folder, build, then **Run** to flash the board (as for the tutorials).
