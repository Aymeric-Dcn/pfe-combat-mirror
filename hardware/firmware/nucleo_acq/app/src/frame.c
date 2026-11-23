/*
 * frame.c
 *
 * Converts each ADC scan to millivolts and queues it as a binary frame.
 * FRAME_Queue() is called from the DMA interrupt (2kHz), FRAME_Send()
 * from the main loop sends the queue to USART2 by DMA.
 */

#include "frame.h"
#include "bsp.h"

// Internal reference calibration value, measured by ST at VDDA = 3.3V
#define VREFINT_CAL		(*(uint16_t *)0x1FFFF7BA)

// About 60ms of frames
#define TX_BUFFER_SIZE	2048

static uint8_t				tx_buffer[TX_BUFFER_SIZE];
static volatile uint16_t	tx_head = 0;		// written by FRAME_Queue()
static volatile uint16_t	tx_tail = 0;		// written by FRAME_Send()
static uint16_t				tx_length = 0;		// transfer in progress
static uint16_t				frame_counter = 0;

volatile uint16_t			frames_dropped = 0;


void FRAME_Queue(uint16_t *adc_scan)
{
	uint8_t		frame[FRAME_LENGTH];
	uint32_t	vdda_mv;
	uint32_t	mv;
	uint8_t		checksum = 0;
	uint16_t	head, used;
	uint8_t		i;

	// VDDA from the internal reference (last channel of the scan)
	vdda_mv = 3300;
	if (adc_scan[5] != 0)
	{
		vdda_mv = 3300 * (uint32_t)VREFINT_CAL / adc_scan[5];
	}

	// Sync word and counter
	frame[0] = 0xA5;
	frame[1] = 0x5A;
	frame[2] = frame_counter & 0xFF;
	frame[3] = frame_counter >> 8;
	frame_counter++;

	// 4 sensors and V_REF in millivolts
	for (i=0; i<5; i++)
	{
		mv = ((uint32_t)adc_scan[i] * vdda_mv + 2047) / 4095;
		frame[4 + 2*i] = mv & 0xFF;
		frame[5 + 2*i] = mv >> 8;
	}
	frame[14] = vdda_mv & 0xFF;
	frame[15] = vdda_mv >> 8;

	for (i=2; i<FRAME_LENGTH-1; i++)
	{
		checksum += frame[i];
	}
	frame[FRAME_LENGTH-1] = checksum;

	// Copy into the circular buffer, or drop the frame if it is full
	head = tx_head;
	used = (head - tx_tail + TX_BUFFER_SIZE) % TX_BUFFER_SIZE;

	if ((TX_BUFFER_SIZE - 1 - used) < FRAME_LENGTH)
	{
		frames_dropped++;
		return;
	}

	for (i=0; i<FRAME_LENGTH; i++)
	{
		tx_buffer[head] = frame[i];
		head = (head + 1) % TX_BUFFER_SIZE;
	}
	tx_head = head;
}


void FRAME_Skip()
{
	// Keep the counter running so that the PC counts the dropped scan as a gap
	frame_counter++;
}


void FRAME_Send()
{
	uint16_t	head;
	uint16_t	length;

	// Nothing more to do while the previous transfer is running
	if ((tx_length != 0) && ((DMA1->ISR & DMA_ISR_TCIF4) == 0))
	{
		return;
	}

	// Previous transfer done: release its bytes
	tx_tail = (tx_tail + tx_length) % TX_BUFFER_SIZE;
	tx_length = 0;

	head = tx_head;
	if (head == tx_tail)
	{
		return;
	}

	// Send the contiguous part of the queue
	if (head > tx_tail)
	{
		length = head - tx_tail;
	}
	else
	{
		length = TX_BUFFER_SIZE - tx_tail;
	}

	if (BSP_Console_SendDMA(&tx_buffer[tx_tail], length) == 1)
	{
		tx_length = length;
	}
}
