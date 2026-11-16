/*
 * frame.h
 *
 * Binary frames sent to the PC (force plate acquisition)
 */

#ifndef INC_FRAME_H_
#define INC_FRAME_H_

#include "stm32f0xx.h"

/*
 * Frame: 17 bytes, little endian
 * 0xA5 0x5A | counter u16 | sensor 1..4 mV | V_REF mV | VDDA mV | checksum u8
 * checksum = sum of the 14 bytes between the sync word and itself, mod 256
 */

#define FRAME_LENGTH	17

void	FRAME_Queue		(uint16_t *adc_scan);
void	FRAME_Send		(void);

#endif /* INC_FRAME_H_ */
