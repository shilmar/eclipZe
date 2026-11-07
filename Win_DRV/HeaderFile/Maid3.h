//================================================================================================
// Copyright Nikon Electronic Imaging - All rights reserved
//
//
// View this file in a non-proportional font, tabs = 3
//
//================================================================================================
//
// MODULAR ACQUISITION INTERFACE DEFINITION (MAID)
// This header file provides definitions and typedefs for the Nikon MAID 3.0
// interface standard software API.  All clients and modules should include this file.
//
// Specification version: v3.1, r19
// Header file version: v3.1, r20
//
//================================================================================================

#if defined(_MAID_) || defined(_MAID2)
#error Only MAID.H, MAID2.H, or MAID3.H may be included.
#endif

#ifndef _MAID3_		// We only want to be included once
#define _MAID3_

#ifndef RC_INVOKED		// exclude this section for Windows resource compiler
#include "NkTypes.h"		// Special cross-platform typedefs and macros

#ifdef _WIN32
//		#ifndef WIN32
//			#error MAID3 requires WIN32 compilation.
//		#endif

#include <crtdbg.h>	// debug memory use
#pragma pack(push,2)
#define W32EXPORT	__declspec(dllexport)
#define CALLPASCAL
#include <windowsx.h>
#else
#define CALLPASCAL
#define W32EXPORT
#define WINAPI
#define CALLBACK
#endif
#ifdef _WIN32
#define AFAREASIZE 96
#else
#define AFAREASIZE 96
#endif
	//================================================================================================
	/*														STRUCTURE DEFINITIONS											*/
	//================================================================================================
	// This file declares structures that are all 4-byte aligned. Even flags are declared as ULONGs
	// in order to preserve the alignment (maximum efficiency on most CPUs).
	// Double precision floating point numbers (DOUB_P) must be 8-byte numbers (64-bit IEEE).
	//	All strings are C format strings (terminated by 0 byte)
	//================================================================================================

typedef LPVOID		LPNKFUNC;

typedef struct tagNkMAIDCallback
{
	LPNKFUNC	pProc;
	NKREF		refProc;
} NkMAIDCallback, FAR* LPNkMAIDCallback;

typedef struct tagNkMAIDDateTime
{
	UWORD nYear;				// ie 1997, 1998
	UWORD nMonth;				// 0-11 = Jan-Dec
	UWORD nDay;					// 1-31
	UWORD nHour;				// 0-23
	UWORD nMinute;				// 0-59
	UWORD nSecond;				// 0-59
	ULONG nSubsecond;			// Module dependent
} NkMAIDDateTime, FAR* LPNkMAIDDateTime;

typedef struct tagNkMAIDPoint
{
	SLONG	x;
	SLONG	y;
} NkMAIDPoint, FAR* LPNkMAIDPoint;

typedef struct tagNkMAIDSize
{
	ULONG	w;
	ULONG	h;
} NkMAIDSize, FAR* LPNkMAIDSize;

typedef struct tagNkMAIDRect
{
	SLONG	x;						// left coordinate
	SLONG	y;						// top coordinate
	ULONG	w;						// width
	ULONG	h;						// height
} NkMAIDRect, FAR* LPNkMAIDRect;

typedef struct tagNkMAIDString
{
	SCHAR	str[256];			// allows a 255 character null terminated string
} NkMAIDString, FAR* LPNkMAIDString;

typedef struct tagNkMAIDArray
{
	ULONG		ulType;				// one of eNkMAIDArrayType
	ULONG		ulElements;			// total number of elements
	ULONG		ulDimSize1;			// size of first dimention
	ULONG		ulDimSize2;			// size of second dimention, zero for 1 dim
	ULONG		ulDimSize3;			// size of third dimention, zero for 1 or 2 dim
	UWORD		wPhysicalBytes;	// bytes per element
	UWORD		wLogicalBits;		// must be <= wPhysicalBytes * 8
	LPVOID	pData;				// allocated by the client
} NkMAIDArray, FAR* LPNkMAIDArray;

typedef struct tagNkMAIDEnum
{
	ULONG		ulType;				// one of eNkMAIDArrayType
	ULONG		ulElements;			// total number of elements
	ULONG		ulValue;				// current index
	ULONG		ulDefault;			// default index
	SWORD		wPhysicalBytes;	// bytes per element
	LPVOID	pData;				// allocated by the client
} NkMAIDEnum, FAR* LPNkMAIDEnum;

typedef struct tagNkMAIDRange
{
	DOUB_P		lfValue;
	DOUB_P		lfDefault;
	ULONG			ulValueIndex;
	ULONG			ulDefaultIndex;
	DOUB_P		lfLower;
	DOUB_P		lfUpper;
	ULONG			ulSteps;			// zero for infinite range, otherwise must be >= 2
} NkMAIDRange, FAR* LPNkMAIDRange;

typedef struct tagNkMAIDCapInfo
{
	ULONG	ulID;						// one of eNkMAIDCapability or vendor specified
	ULONG	ulType;					// one of eNkMAIDCapabilityType
	ULONG	ulVisibility;			// eNkMAIDCapVisibility bits
	ULONG	ulOperations;			// eNkMAIDCapOperations bits
	SCHAR	szDescription[256];	// text describing the capability
} NkMAIDCapInfo, FAR* LPNkMAIDCapInfo;

typedef struct tagNkMAIDObject
{
	ULONG	ulType;			// One of eNkMAIDObjectType
	ULONG	ulID;
	NKREF	refClient;
	NKREF	refModule;
} NkMAIDObject, FAR* LPNkMAIDObject;

typedef struct tagNkMAIDUIRequestInfo
{
	ULONG				ulType;			// one of eNkMAIDUIReqestType
	ULONG				ulDefault;		// default return value one of eNkMAIDUIRequestResult
	BOOL				fSync;			// TRUE if user must respond before returning
	SCHAR FAR* lpPrompt;		// NULL terminated text to show to user
	SCHAR FAR* lpDetail;		// NULL terminated text indicating more detail
	LPNkMAIDObject	pObject;			// module, source, item, or data object
	NKPARAM			data;				// Pointer to an NkMAIDArray structure
} NkMAIDUIRequestInfo, FAR* LPNkMAIDUIRequestInfo;

typedef struct tagNkMAIDDataInfo
{
	ULONG		ulType;				// one of eNkMAIDDataObjType
} NkMAIDDataInfo, FAR* LPNkMAIDDataInfo;

typedef struct tagNkMAIDImageInfo
{
	NkMAIDDataInfo	base;
	NkMAIDSize	szTotalPixels;	// total size of image to be transfered
	ULONG			ulColorSpace;	// One of eNkMAIDColorSpace
	NkMAIDRect	rData;			// Coords of data, (0,0) = top,left
	ULONG			ulRowBytes;		// number of bytes per row of pixels
	UWORD			wBits[4];		// number of bits per plane per pixel
	UWORD			wPlane;			// Plane of the image being delivered
	BOOL			fRemoveObject;	// TRUE if the object should be removed
} NkMAIDImageInfo, FAR* LPNkMAIDImageInfo;

typedef struct tagNkMAIDSoundInfo
{
	NkMAIDDataInfo	base;
	ULONG		ulTotalSamples;	// number of full samples to be transferred
	BOOL		fStereo;				// TRUE if stereo, FALSE if mono
	ULONG		ulStart;				// index of starting sample of data
	ULONG		ulLength;			// number of samples of data
	UWORD		wBits;				// number of bits per channel
	UWORD		wChannel;			// 0 = mono or L+R; 1,2 = left, right
	BOOL		fRemoveObject;		// TRUE if the object should be removed
} NkMAIDSoundInfo, FAR* LPNkMAIDSoundInfo;

typedef struct tagNkMAIDFileInfo
{
	NkMAIDDataInfo	base;
	ULONG				ulFileDataType;	// One of eNkMAIDFileDataTypes
	ULONG				ulTotalLength;		// total number of bytes to be transferred
	ULONG				ulStart;				// index of starting byte (0-based)
	ULONG				ulLength;			// number of bytes in this delivery
	BOOL				fDiskFile;			// TRUE if the file is delivered on disk
	BOOL				fRemoveObject;		// TRUE if the object should be removed
} NkMAIDFileInfo, FAR* LPNkMAIDFileInfo;

#endif	// (of #ifndef RC_INVOKED)

//Simplified API 
union SIZEINFO
{
	char cSize[2];
	unsigned short uiSize;
};

typedef struct
{
	SIZEINFO Integer;
	SIZEINFO Decimal;
} stSpiritLevel;

typedef struct
{
	char m_cHours;
	char m_cMinutes;
	char m_cSeconds;
	char m_cFrame;
} CTimeCode;

typedef struct tagLiveViewHeader
{
	char            m_cLVImageCompression;
	char			m_cAFEnable;
	char			m_cAFDriveStatus;
	char			m_cFocused;
	char			m_cFaceRecognition;
	char			m_cFaceRecogNum;
	char			m_cFaceRecogIdx;
	char            m_cTrackingAFStatus;
	unsigned char	m_MovieRemainTime[4];
	char			m_MicrophoneIndicatorPeakL;
	char			m_MicrophoneIndicatorPeakR;
	char			m_MicrophoneIndicatorL;
	char			m_MicrophoneIndicatorR;
	char			m_MovieRecState;//Movie recording information 0: During LV execution 1: During movie recording
	char			m_cHDMIRecStatus;//State of synchronous recording by the external recorder 0: Synchronous recording cannot be performed
	//1 : Synchronous recording standby(Synchronous recording can be performed but does not start) 2 : Synchronous recording is being performed
	char            m_cTimeCodeStatus;
	char			m_cSpotWbState;
	char			m_cRotation;
	char			m_LiveViewWBStatus;//Using white balance for live view photography 0: Off 1 : On

	WORD 			nMajorVersion;
	WORD 			nMinorVersion;

	SIZEINFO		m_TimeRemain;
	SIZEINFO		m_TotalW;
	SIZEINFO		m_TotalH;
	SIZEINFO		m_DispAreaW;
	SIZEINFO		m_DispAreaH;
	SIZEINFO		m_DispCenterW;
	SIZEINFO		m_DispCenterH;
	SIZEINFO		m_JpegW;
	SIZEINFO		m_JpegH;
	SIZEINFO		m_AFFrameSizeW;
	SIZEINFO		m_AFFrameSizeH;
	SIZEINFO		m_AFCenterW;
	SIZEINFO		m_AFCenterH;
	SIZEINFO		m_FaceRecogAF_FrameW[AFAREASIZE];
	SIZEINFO		m_FaceRecogAF_FrameH[AFAREASIZE];
	SIZEINFO		m_FaceRecogAF_CenterX[AFAREASIZE];
	SIZEINFO		m_FaceRecogAF_CenterY[AFAREASIZE];

	CTimeCode		m_stTimeCode;

	uint32_t		LvShowInfoLength;
	uint32_t		LvImageLength;

	stSpiritLevel	m_SpiritLevel[3];

	char			m_cPictureTakingTemperatureStatus; //0:Normal  1: middle temperature(low) 2 : Middle temperature(height)
	//3 : High temperature 4 : Countdown display
	char			m_cReserved1[3];
	uint32_t		m_MovieRemainTimeMSec;
	uint32_t		m_MovieElapsedTimeMec;
	char			m_cMovieElapsedTimeApplicable; //0: No 1: Yes
	char			m_cReserved2[3];
	uint32_t		m_AngleRollInteger;
	uint32_t		m_AngleRollDecimal; //Divide by 10000 to get decimal
	uint32_t		m_AnglePichInteger;
	uint32_t		m_AnglePichDecimal; //Divide by 10000 to get decimal
	uint32_t		m_AngleYawInteger;
	uint32_t		m_AngleYawDecimal; //Divide by 10000 to get decimal
}NKMAIDLiveViewHeader, FAR* LPNKMAIDLiveViewHeader;

typedef struct tagNkMAIDLiveViewData
{
	ULONG		ulLvImageSize;	// Size of PIC
	UWORD		wPhysicalBytes;
	UWORD		wLogicalBits;
	NKMAIDLiveViewHeader stLiveViewHeader;
	LPVOID		pImageData;
} NkMAIDLiveViewData, FAR* LPNkMAIDLiveViewData;

typedef struct tagNkMAIDCSCallback
{
	LPNKFUNC   pUIReqProc; //Type - LPMAIDUIRequestProc
	LPNKFUNC   pfnEventProc; //Type - LPMAIDEventProc
	LPNKFUNC   pProgressProc; //Type - LPMAIDProgressProc
	LPNKFUNC   pDataProc;	//Type - LPMAIDDataProc
	LPNKFUNC   pLiveViewDataProc; //Type - LPLiveViewDataProc
	NKREF         refProc;
} NkMAIDCSCallback, FAR* LPNkMAIDCSCallback;

typedef struct tagNkMAIDEnumCapInfo
{
	LPNkMAIDCapInfo pCapArray;
	ULONG ulCapCount;
	ULONG ulAllocationSize;
}NkMAIDEnumCapInfo, FAR* LPNkMAIDEnumCapInfo;

typedef struct tagNkMAIDDeviceInfo
{
	ULONG ID;
	char  Name[64];
	bool  Availability;
	ULONG ulConnectedPID;
	char Version[64];
}NkMAIDDeviceInfo, FAR* LPNkMAIDDeviceInfo;

typedef struct tagNkMAIDEnumDevices
{
	ULONG ulElements; // total number of elements
	ULONG ulValue; // current index			
	LPNkMAIDDeviceInfo pDeviceData; // allocated by the client
} NkMAIDEnumDevices, FAR* LPNkMAIDEnumDevices;

typedef struct tagNkMAIDStringSteps
{
	SCHAR	strCurrentValue[256];			// allows a 255 character null terminated string
	SCHAR	strDefaultValue[256];			// allows a 255 character null terminated string
	ULONG	ulMaxAllowedSteps;  //Maximum allowable steps
	ULONG	ulChangedSteps;     //Steps changed
	ULONG	ulDirection;		//0 - High Side, 1 - Low Side
} NkMAIDStringSteps, FAR* LPNkMAIDStringSteps;

enum eNkMAIDShootingType
{
	kNkSDKShootingTypeSingle = 1,
	kNkSDKShootingTypeContinuous,
	kNkSDKShootingTypeInterval,
	kNkSDKShootingTypeSelfTimer,
	kNkSDKShootingTypeBULB,
	kNkSDKShootingTypeBULBInterval,
	kNkSDKShootingTypeFocusShift,
	kNkSDKShootingTypePixelShift
};

typedef struct tagShootingStructure
{
	eNkMAIDShootingType ShootingType;
	ULONG ulContinuous_Interval_NumShots;
	ULONG ulBULBExposureDuration;
	ULONG ulShootingStartTimeFromNow;
	ULONG ulIntervalTime;
	bool  bAutoFocus;
#ifdef _WIN32
	wchar_t ImageSavePath[1024];
#else
	char ImageSavePath[1024];
#endif
	LPVOID pOutPutRefrence;
}MAIDShootingStructure, FAR* LPNkMAIDShootingStructure;

enum eNkMAIDShootingStatus
{
	kNkSDKShootingFinishedOrNotStarted,
	kNkSDKShootingWaiting,
	kNkSDKShootingExecuting,
	kNkMAIDShootingCancelled,
	kNkMAIDShootingInvalidStatus
};
enum eNkMAIDLoggingLevel
{
	kkNkSDKLogLevel_SystemError = 1,
	kkNkSDKLogLevel_Error,
	kkNkSDKLogLevel_Debug,
};
//Simplified API

	//Change for GUI
enum eNkSDKGetSettingRequestType
{
	kNkSDKGetSettingValue,
	kNkSDKGetSettingSupportedValueArray,
	kNkSDKGetSettingDefaultValue,
	kNkSDKGetCapabilityInfo
};
//Change for GUI

//================================================================================================
//	Entrypoint and callback function definitions
//================================================================================================

#ifdef __cplusplus
extern "C" {	// Tell C++ to use C linking for these functions
#endif

	// Client/Module Interface and Callback Functions
	typedef W32EXPORT NKERROR CALLPASCAL WINAPI MAIDEntryPointProc(
		LPNkMAIDObject	pObject,				// module, source, item, or data object
		ULONG				ulCommand,			// Command, one of eNkMAIDCommand
		ULONG				ulParam,				// parameter for the command
		ULONG				ulDataType,			// Data type, one of eNkMAIDDataType
		NKPARAM			data,					// Pointer or long integer
		LPNKFUNC			pfnComplete,		// Completion function, may be NULL
		NKREF				refComplete);		// Value passed to pfnComplete
	typedef MAIDEntryPointProc FAR* LPMAIDEntryPointProc;

	typedef void CALLPASCAL CALLBACK MAIDCompletionProc(
		LPNkMAIDObject	pObject,				// module, source, item, or data object
		ULONG				ulCommand,			// Command, one of eNkMAIDCommand
		ULONG				ulParam,				// parameter for the command
		ULONG				ulDataType,			// Data type, one of eNkMAIDDataType
		NKPARAM			data,					// Pointer or long integer
		NKREF				refComplete,		// Reference set by client
		NKERROR			nResult);			// One of eNkMAIDResult
	typedef MAIDCompletionProc FAR* LPMAIDCompletionProc;

	typedef NKERROR CALLPASCAL CALLBACK MAIDDataProc(
		NKREF					refClient,		// Reference set by client
		LPVOID				pDataInfo,		// Cast to LPNkMAIDImageInfo or LPNkMAIDSoundInfo
		LPVOID				pData);
	typedef MAIDDataProc FAR* LPMAIDDataProc;

	typedef void CALLPASCAL CALLBACK MAIDEventProc(
		NKREF				refClient,			// Reference set by client
		ULONG				ulEvent,				// One of eNkMAIDEvent
		NKPARAM			data);				// Pointer or long integer
	typedef MAIDEventProc FAR* LPMAIDEventProc;

	typedef void CALLPASCAL CALLBACK MAIDProgressProc(
		ULONG				ulCommand,			// Command, one of eNkMAIDCommand
		ULONG				ulParam,				// parameter for the command
		NKREF				refComplete,		// Reference set by client
		ULONG				ulDone,				// Numerator
		ULONG				ulTotal);			// Denominator
	typedef MAIDProgressProc FAR* LPMAIDProgressProc;

	typedef ULONG CALLPASCAL CALLBACK MAIDUIRequestProc(
		NKREF							refProc,			// reference set by the client
		LPNkMAIDUIRequestInfo	pUIRequest);	// information about the UI request

	typedef MAIDUIRequestProc FAR* LPMAIDUIRequestProc;

	//New Added
	typedef void CALLPASCAL CALLBACK LiveViewDataProc(
		NKREF ref,
		LPNkMAIDLiveViewData pstLiveViewData);
	typedef LiveViewDataProc FAR* LPLiveViewDataProc;
	//New Added

	//Changes for CS Layer
	W32EXPORT NKERROR CALLPASCAL WINAPI MAIDEntryPointE(LPNkMAIDObject pObject, ULONG ulCommand, ULONG ulParam,
		ULONG ulDatatype, NKPARAM data, LPMAIDCompletionProc pProc, NKREF nkRef);
	W32EXPORT BOOL CALLPASCAL WINAPI SetHinstance(HINSTANCE hInstDll, DWORD dwReason, LPVOID lpReserved);
	//Changes for CS Layer


	typedef void* CALLPASCAL CALLBACK MAIDAllocateMemory(
		size_t  memory_size);
	typedef MAIDAllocateMemory FAR* LPMAIDAllocateMemory;

	typedef void CALLPASCAL CALLBACK MAIDFreeMemory(
		void* memory_pointer);
	typedef MAIDFreeMemory FAR* LPMAIDFreeMemory;

	typedef void CALLPASCAL CALLBACK MAIDAsyncCompletionProc(
		NKREF    refComplete,   // Reference set by client
		NKERROR    nResult);    // One of eNkMAIDResult
	typedef MAIDAsyncCompletionProc FAR* LPMAIDAsyncCompletionProc;

	//Changes for CS Layer

	//Simplified API 

	typedef W32EXPORT NKERROR CALLPASCAL WINAPI MAIDInitializeSDK(
		/*[in]*/   LPMAIDAllocateMemory allocMemory, /*Function pointer of memory allocation API.*/
		/*[in]*/   LPMAIDFreeMemory freeMemory, /*Function pointer to memory free API.*/
		/*[in]*/   LPNkMAIDCSCallback callback, /*Callback functions registration (required by CS Layer).*/
		/*[out][in]*/ LPNkMAIDEnumDevices* ppDeviceList,/*GUI will pass the address of LPNkMAIDEnum, If not null,  CS Layer will allocate the required memory and copy  the device List*/
		/*[out][in]*/ LPNkMAIDEnumCapInfo* ppEnumCapInfo /*GUI will pass the address of LPNkMAIDEnumCapInfo, If not null, CS Layer will allocate the required memory and copy the module related capabilities */
	);
	typedef MAIDInitializeSDK FAR* LPMAIDInitializeSDKProc;

	typedef W32EXPORT HRESULT CALLPASCAL WINAPI MAIDFreeSDK();
	typedef MAIDFreeSDK FAR* LPMAIDFreeSDKProc;

	typedef W32EXPORT NKERROR CALLPASCAL WINAPI MAIDConnectDevice(
		/*[in]*/  ULONG ulDeviceId, /*Device Id for session openining*/
		/*[out][in]*/ LPNkMAIDEnumCapInfo* ppEnumCapInfo /*GUI will pass the address of LPNkMAIDEnumCapInfo, If not null, CS Layer will allocate the required memory and copy all capabilities */
	);
	typedef MAIDConnectDevice FAR* LPMAIDConnectDeviceProc;

	typedef W32EXPORT HRESULT CALLPASCAL WINAPI MAIDDisconnectDevice();
	typedef MAIDDisconnectDevice FAR* LPMAIDDisconnectDeviceProc;

	typedef W32EXPORT NKERROR CALLPASCAL WINAPI MAIDStartLiveView(
		/*[out][in]*/ LPMAIDAsyncCompletionProc pProc,    /*To judge Api call is sync or async,not null means Async."pProc" will be called after completion of Api*/
		/*[in]*/NKREF nkRef     /*reference set by GUI*/
	);
	typedef MAIDStartLiveView FAR* LPMAIDStartLiveView;

	typedef W32EXPORT NKERROR CALLPASCAL WINAPI MAIDStopLiveView(
		/*[out][in]*/ LPMAIDAsyncCompletionProc pProc,    /*To judge Api call is sync or async,not null means Async."pProc" will be called after completion of Api*/
		/*[in]*/NKREF nkRef     /*reference set by GUI*/
	);
	typedef MAIDStopLiveView FAR* LPMAIDStopLiveView;

	enum eNkMAIDLVStatus
	{
		eNkMAIDLVStatus_OFF = 0,
		eNkMAIDLVStatus_ON,
		eNkMAIDLVStatus_ON_Menu,
		eNkMAIDLVStatus_ON_RemoteLV,
		eNkMAIDLVStatus_ON_CameraLV
	};

	// kNkMAIDCapability_LiveViewStatus(0x823e)
	enum eNkMAIDLiveViewStatus;

	typedef W32EXPORT NKERROR CALLPASCAL WINAPI MAIDGetLiveViewStatus(
		/*[out][in]*/ eNkMAIDLVStatus& LiveViewStatus/*CS Layer will fill one of the value  of*/
	);
	typedef MAIDGetLiveViewStatus FAR* LPMAIDGetLiveViewStatus;

	typedef W32EXPORT NKERROR CALLPASCAL WINAPI MAIDStartShooting(
		/*[in]*/ MAIDShootingStructure& stShootParam,/*GUI will send information in structure required for shooting*/
		/*[out][in]*/ LPMAIDAsyncCompletionProc pProc,    /*To judge Api call is sync or async,not null means Async.""pProc"" will be called after completion of Api*/
		/*[in]*/NKREF nkRef     /*reference set by GUI*/);
	typedef MAIDStartShooting FAR* LPMAIDStartShooting;


	typedef W32EXPORT NKERROR CALLPASCAL WINAPI MAIDCancelShooting(
		/*[out][in]*/ LPMAIDAsyncCompletionProc pProc,    /*To judge Api call is sync or async,not null means Async.""pProc"" will be called after completion of Api*/
		/*[in]*/NKREF nkRef     /*reference set by GUI*/);
	typedef MAIDCancelShooting FAR* LPMAIDCancelShooting;


	typedef W32EXPORT HRESULT CALLPASCAL WINAPI MAIDGetShootingStatus(
		/*[out][in]*/ eNkMAIDShootingStatus& ShootingStatus/*CS Layer will fill one of the value  of*/);
	typedef MAIDGetShootingStatus FAR* LPMAIDGetShootingStatus;

	typedef W32EXPORT HRESULT CALLPASCAL WINAPI MAIDGetRemainingShootCount(
		/*[out][in]*/ ULONG& RemShootCount/*ULONG variable. In case of continuous shooting and interval shooting CS Layer will retuen the value.*/);
	typedef MAIDGetRemainingShootCount FAR* LPMAIDGetRemainingShootCount;

	enum eNkMAIDDataType;
	typedef W32EXPORT NKERROR CALLPASCAL WINAPI MAIDGetCapability(
		/*[in]*/ULONG ulCapabilityId, /*Capability Id to get*/
		/*[in]*/eNkSDKGetSettingRequestType eType, /*One of the value of
		/*[out][in]*/LPVOID& pDataPtr, /*ppDataPtr to send data to GUI.CS Layer will allocate the required memory and copy the data*/
		/*[out][in]*/eNkMAIDDataType& ulDataType /*ulDataType to return eNkMAIDDataType*/);
	typedef MAIDGetCapability FAR* LPMAIDGetCapability;

	typedef W32EXPORT NKERROR CALLPASCAL WINAPI MAIDSetCapability(
		/*[in]*/ULONG ulCapabilityId, /*Capability Id to change value*/
		/*[in]*/LPVOID pData, /*pData is being new value of capability*/
		/*[out][in]*/eNkMAIDDataType ulDataType /*ulDataType to determine data type of pData */);
	typedef MAIDSetCapability FAR* LPMAIDSetCapability;

	typedef W32EXPORT NKERROR CALLPASCAL WINAPI MAIDEnumCapabilities(
		/*[out][in]*/LPNkMAIDEnumCapInfo& pEnumCapInfo, /*pEnumCapInfo to get all the capability information with capability count. CS Layer will allocate required memory and copy the data*/
		/*[out][in]*/ LPMAIDAsyncCompletionProc pProc,    /*To judge Api call is sync or async,not null means Async.""pProc"" will be called after completion of Api*/
		/*[in]*/NKREF nkRef     /*reference set by GUI*/);
	typedef MAIDEnumCapabilities FAR* LPMAIDEnumCapabilities;

	typedef W32EXPORT NKERROR CALLPASCAL WINAPI MAIDEnumDevices(
		/*[out][in]*/LPNkMAIDEnumDevices& pEnumDeviceInfo, /*pEnumDeviceInfo to get all the device information with device count and availability info. CS Layer will allocate required memory and copy the data*/
		/*[out][in]*/ LPMAIDAsyncCompletionProc pProc,    /*To judge Api call is sync or async,not null means Async.""pProc"" will be called after completion of Api*/
		/*[in]*/NKREF nkRef     /*reference set by GUI*/);
	typedef MAIDEnumDevices FAR* LPMAIDEnumDevices;

	typedef W32EXPORT HRESULT CALLPASCAL WINAPI MAIDGetLoggingLevel(
		/*[out][in]*/  eNkMAIDLoggingLevel& LoggingLevel/*CS Layer will fill one of the value  of*/);
	typedef MAIDGetLoggingLevel FAR* LPMAIDGetLoggingLevel;

	typedef W32EXPORT NKERROR CALLPASCAL WINAPI MAIDSetLoggingLevel(
		/*[in]*/  eNkMAIDLoggingLevel LoggingLevel/*CS Layer will set one of the value  of*/);
	typedef MAIDSetLoggingLevel FAR* LPMAIDSetLoggingLevel;

	typedef W32EXPORT NKERROR CALLPASCAL WINAPI MAIDStartMovieRecording(
		/*[in]*/ LPSTR sPath,  /*Path to save video file*/
		/*[out][in]*/ LPMAIDAsyncCompletionProc pProc,    /*To judge Api call is sync or async,not null means Async.""pProc"" will be called after completion of Api*/
		/*[in]*/NKREF nkRef     /*reference set by GUI*/);
	typedef MAIDStartMovieRecording FAR* LPMAIDStartMovieRecording;

	typedef W32EXPORT NKERROR CALLPASCAL WINAPI MAIDStopMovieRecording(
		/*[out][in]*/ LPMAIDAsyncCompletionProc pProc,    /*To judge Api call is sync or async,not null means Async.""pProc"" will be called after completion of Api*/
		/*[in]*/NKREF nkRef     /*reference set by GUI*/);
	typedef MAIDStopMovieRecording FAR* LPMAIDStopMovieRecording;

	typedef W32EXPORT NKERROR CALLPASCAL WINAPI MAIDStartOperation(
		/*[in]*/ULONG ulCapabilityId, /*Capability Id to get*/
		/*[out][in]*/ LPMAIDAsyncCompletionProc pProc,    /*To judge Api call is sync or async,not null means Async.""pProc"" will be called after completion of Api*/
		/*[in]*/NKREF nkRef     /*reference set by GUI*/);
	typedef MAIDStartOperation FAR* LPMAIDStartOperation;

	typedef W32EXPORT NKERROR CALLPASCAL WINAPI MAIDMarkAsynCallSequence();
	typedef MAIDMarkAsynCallSequence FAR* LPMAIDMarkAsynCallSequence;

	typedef W32EXPORT NKERROR CALLPASCAL WINAPI MAIDAbortAsynCallOrSequence(
		/*[in]*/ BOOL AbortToMark,  /*To judge abort command upto Mark or all command, True means abort command  till mark*/
		/*[out][in]*/ LPMAIDAsyncCompletionProc pProc,    /*To judge Api call is sync or async,not null means Async.""pProc"" will be called after completion of Api*/
		/*[in]*/NKREF nkRef     /*reference set by GUI*/);
	typedef MAIDAbortAsynCallOrSequence FAR* LPMAIDAbortAsynCallOrSequence;

#ifdef _WIN32
	typedef W32EXPORT NKERROR CALLPASCAL WINAPI MAIDSetImageVideoSavePath(
		const wchar_t* pImageSavePath  /*Image file save path*/,
		const wchar_t* pVideoSavePath /*Video file save path*/);
#else
	typedef W32EXPORT NKERROR CALLPASCAL WINAPI MAIDSetImageVideoSavePath(
		const char* pImageSavePath, /*Image file save path*/
		const char* pVideoSavePath /*Video file save path*/);
#endif
	typedef MAIDSetImageVideoSavePath FAR* LPMAIDSetImageVideoSavePath;

	typedef W32EXPORT BOOL CALLPASCAL WINAPI MAIDIsDeviceFullSupport();
	typedef MAIDIsDeviceFullSupport FAR* LPMAIDIsDeviceFullSupport;

	//Simplified API

#ifdef __cplusplus
}
#endif


//===================================================================================================
/*														CONSTANT DEFINITIONS													*/
//===================================================================================================

// The module will deliver one of these values to the nResult parameter of the clients
// completion callback function and return the same value from the entry point. Errors
// will have negative values.
enum eNkMAIDResult
{
	// these values are errors
	kNkMAIDResult_NotSupported = -127,
	kNkMAIDResult_UnexpectedDataType,
	kNkMAIDResult_ValueOutOfBounds,
	kNkMAIDResult_BufferSize,
	kNkMAIDResult_Aborted,
	kNkMAIDResult_NoMedia,
	kNkMAIDResult_NoEventProc,
	kNkMAIDResult_NoDataProc,
	kNkMAIDResult_ZombieObject,
	kNkMAIDResult_OutOfMemory,
	kNkMAIDResult_UnexpectedError,
	kNkMAIDResult_HardwareError,
	kNkMAIDResult_MissingComponent,
	//New Error code
	kNkMAIDAPIResult_DeviceNotAvailable,
	kNkMAIDAPIResult_OpenSessionFailed,
	kNkMAIDAPIResult_LiveViewAlreadyStarted,
	kNkMAIDAPIResult_LiveViewAlreadyStopped,
	kNkMAIDAPIResult_InvalidDeviceID,
	kNkMAIDAPIResult_StartLiveViewFailed,
	kNkMAIDAPIResult_DeviceFailed,
	kNkMAIDAPIResult_CapabilityNotSupported,
	kNkMAIDAPIResult_OperationNotSupported,
	kNkMAIDAPIResult_InvalidCapID,
	kNkMAIDAPIResult_OutOfRangeValue,
	kNkMAIDAPIResult_InvalidShootingType,
	kNkMAIDAPIResult_ShootingCancelFailed,
	kNkMAIDAPIResult_InvalidShootCount,
	kNkMAIDAPIResult_InvalidShootingMode,
	kNkMAIDAPIResult_InvalidFileSavePath,
	kNkMAIDAPIResult_MovieStartFailed,
	kNkMAIDAPIResult_FileSaveFailed,
	kNkMAIDAPIResult_InvalidInterval, //Change
	kNkMAIDAPIResult_InvalidStartTime, //Change
	kNkMAIDAPIResult_InvalidBULBExposureTime, //Change
	kNkMAIDAPIResult_InvalidArguments, //Change
	kNkMAIDAPIResult_InvalidState, //Change
	kNkMAIDAPIResult_ContinousShootIntrupted,
	//New  Error code
	kNkMAIDResult_NoError = 0,

	// these values are warnings
	kNkMAIDResult_Pending,
	kNkMAIDResult_OrphanedChildren,

	kNkMAIDResult_VendorBase = +127
};

// The module will use one or more of these values to indicate what types of data a module
// or source can produce and what types of data are available for a specific item.
enum eNkMAIDDataObjType
{
	kNkMAIDDataObjType_Image = 0x00000001,
	kNkMAIDDataObjType_Sound = 0x00000002,
	kNkMAIDDataObjType_Video = 0x00000004,
	kNkMAIDDataObjType_Thumbnail = 0x00000008,
	kNkMAIDDataObjType_File = 0x00000010
};

// The client will pass one of these values to the ulDataType parameter of the entry point
// to indicate how the data parameter will be interpreted by the module.
enum eNkMAIDDataType
{
	kNkMAIDDataType_Null = 0,
	kNkMAIDDataType_Boolean,			// passed by value, set only
	kNkMAIDDataType_Integer,			// signed 32 bit int, passed by value, set only
	kNkMAIDDataType_Unsigned,			// unsigned 32 bit int, passed by value, set only
	kNkMAIDDataType_BooleanPtr,		// pointer to single byte boolean value(s)
	kNkMAIDDataType_IntegerPtr,		// pointer to signed 4 byte value(s)
	kNkMAIDDataType_UnsignedPtr,		// pointer to unsigned 4 byte value(s)
	kNkMAIDDataType_FloatPtr,			// pointer to DOUB_P value(s)
	kNkMAIDDataType_PointPtr,			// pointer to NkMAIDPoint structure(s)
	kNkMAIDDataType_SizePtr,			// pointer to NkMAIDSize structure(s)
	kNkMAIDDataType_RectPtr,			// pointer to NkMAIDRect structure(s)
	kNkMAIDDataType_StringPtr,			// pointer to NkMAIDString structure(s)
	kNkMAIDDataType_DateTimePtr,		// pointer to NkMAIDDateTime structure(s)
	kNkMAIDDataType_CallbackPtr,		// pointer to NkMAIDCallback structure(s)
	kNkMAIDDataType_RangePtr,			// pointer to NkMAIDRange structure(s)
	kNkMAIDDataType_ArrayPtr,			// pointer to NkMAIDArray structure(s)
	kNkMAIDDataType_EnumPtr,			// pointer to NkMAIDEnum structure(s)
	kNkMAIDDataType_ObjectPtr,			// pointer to NkMAIDObject structure(s)
	kNkMAIDDataType_CapInfoPtr,		// pointer to NkMAIDCapInfo structure(s)
	kNkMAIDDataType_GenericPtr,			// pointer to generic data
	kNkMAIDDataType_StringStepsPtr
};

// The module will set one of these values in the ulType member of the NkMAIDArray structure
// to indicate how the data of the array should be interpreted.
enum eNkMAIDArrayType
{
	kNkMAIDArrayType_Boolean = 0,		// 1 byte per element
	kNkMAIDArrayType_Integer,			// signed value that is 1, 2 or 4 bytes per element
	kNkMAIDArrayType_Unsigned,			// unsigned value that is 1, 2 or 4 bytes per element
	kNkMAIDArrayType_Float,				// DOUB_P elements
	kNkMAIDArrayType_Point,				// NkMAIDPoint structures
	kNkMAIDArrayType_Size,				// NkMAIDSize structures
	kNkMAIDArrayType_Rect,				// NkMAIDRect structures
	kNkMAIDArrayType_PackedString,	// packed array of strings
	kNkMAIDArrayType_String,			// NkMAIDString structures
	kNkMAIDArrayType_DateTime			// NkMAIDDateTime structures
};

// The module will set one of these values in the ulType member of the NkMAIDCapInfo structure
// to indicate what type of information is represented.
enum eNkMAIDCapType
{
	kNkMAIDCapType_Process = 0,	// a process that can be started
	kNkMAIDCapType_Boolean,			// single byte boolean value
	kNkMAIDCapType_Integer,			// signed 4 byte value
	kNkMAIDCapType_Unsigned,		// unsigned 4 byte value
	kNkMAIDCapType_Float,			// DOUB_P value
	kNkMAIDCapType_Point,			// NkMAIDPoint structure
	kNkMAIDCapType_Size,				// NkMAIDSize structure
	kNkMAIDCapType_Rect,				// NkMAIDRect structure
	kNkMAIDCapType_String,			// NkMAIDString structure
	kNkMAIDCapType_DateTime,		// NkMAIDDateTime structure
	kNkMAIDCapType_Callback,		// NkMAIDCallback structure
	kNkMAIDCapType_Array,			// NkMAIDArray structure
	kNkMAIDCapType_Enum,				// NkMAIDEnum structure
	kNkMAIDCapType_Range,			// NkMAIDRange structure
	kNkMAIDCapType_Generic,			// generic data
	kNkMAIDCapType_BoolDefault,		// Reserved
	kNkMAIDCapType_StringSteps
};

// The module will set one of more of these values in the ulOperations member of the
// NkMAIDCapInfo structure to indicate what operations are permitted on a particular capability.
enum eNkMAIDCapOperations
{
	kNkMAIDCapOperation_Start = 0x0001,
	kNkMAIDCapOperation_Get = 0x0002,
	kNkMAIDCapOperation_Set = 0x0004,
	kNkMAIDCapOperation_GetArray = 0x0008,
	kNkMAIDCapOperation_GetDefault = 0x0010
};

// The module will set one or more of these values in the ulVisibility member of the
// NkMAIDCapInfo structure to indicate what level of visibility a particular capability has.
enum eNkMAIDCapVisibility
{
	kNkMAIDCapVisibility_Hidden = 0x0001,
	kNkMAIDCapVisibility_Advanced = 0x0002,
	kNkMAIDCapVisibility_Vendor = 0x0004,
	kNkMAIDCapVisibility_Group = 0x0008,
	kNkMAIDCapVisibility_GroupMember = 0x0010,
	kNkMAIDCapVisibility_Invalid = 0x0020
};

// The module will set one of these values in the ulType member of the NkMAIDObject structure
// to indicate what type of object is represented.
enum eNkMAIDObjectType
{
	kNkMAIDObjectType_Module = 1,
	kNkMAIDObjectType_Source,
	kNkMAIDObjectType_Item,
	kNkMAIDObjectType_DataObj
};

// The module will deliver one of these values to the ulEvent parameter of the clients event
// callback function to indicate what event has occurred.
enum eNkMAIDEvent
{
	kNkMAIDEvent_AddChild,
	kNkMAIDEvent_RemoveChild,
	kNkMAIDEvent_WarmingUp,
	kNkMAIDEvent_WarmedUp,
	kNkMAIDEvent_CapChange,
	kNkMAIDEvent_OrphanedChildren,
	kNkMAIDEvent_CapChangeValueOnly,
	kNkMAIDEvent_DeviceInfoChanged,  //Added New
	kNkMAIDEvent_ImageSaved,          //Added New
	kNkMAIDEvent_ImageSavedInCard, //Added New
	kNkMAIDEvent_StorageFull_ImageNotSaved, //Added New
	kNkMAIDEvent_AcquireFailed_ImageNotSaved, //Added New
	kNkMAIDEvent_ChangeSaveDestination,
	kNkMAIDEvent_AddImageInCard
};

// When the module calls the clients user interface callback function, the ulType member of
// the NkMAIDUIRequestInfo structure will be set to one of these values. The user will be
// presented with the choices specified by the value.
enum eNkMAIDUIRequestType
{
	kNkMAIDUIRequestType_Ok,
	kNkMAIDUIRequestType_OkCancel,
	kNkMAIDUIRequestType_YesNo,
	kNkMAIDUIRequestType_YesNoCancel
};

// When the module calls the clients user interface callback function, the ulDefault member
// of the NkMAIDUIRequestInfo structure will be set to one of these values.  The value will
// indicate which button should be highlighted by default.  The clients user interface callback
// function will return one of these values depending on which button the user presses.
// The kNkMAIDEventResult_None value can only be returned if the fSync member of the
// NkMAIDUIRequestInfo structure is FALSE.
enum eNkMAIDUIRequestResult
{
	kNkMAIDUIRequestResult_None,
	kNkMAIDUIRequestResult_Ok,
	kNkMAIDUIRequestResult_Cancel,
	kNkMAIDUIRequestResult_Yes,
	kNkMAIDUIRequestResult_No
};

// The module will use one or more of these values in the kNkMAIDCapability_Filter capability.
enum eNkMAIDFilter
{
	kNkMAIDFilter_White,
	kNkMAIDFilter_Infrared,
	kNkMAIDFilter_Red,
	kNkMAIDFilter_Green,
	kNkMAIDFilter_Blue,
	kNkMAIDFilter_Ultraviolet
};

// The client will pass one of these values to the ulCommand parameter of the MAID entry point
// to indicate what operation the module should perform.
enum eNkMAIDCommand
{
	kNkMAIDCommand_Async,			// process asynchronous operations
	kNkMAIDCommand_Open,				// opens a child object
	kNkMAIDCommand_Close,			// closes a previously opened object
	kNkMAIDCommand_GetCapCount,	// get number of capabilities of an object
	kNkMAIDCommand_GetCapInfo,		// get capabilities of an object
	kNkMAIDCommand_CapStart,		// starts capability
	kNkMAIDCommand_CapSet,			// set value of capability
	kNkMAIDCommand_CapGet,			// get value of capability
	kNkMAIDCommand_CapGetDefault,	// get default value of capability
	kNkMAIDCommand_CapGetArray,	// get data for array capability
	kNkMAIDCommand_Mark,				// insert mark in the command queue
	kNkMAIDCommand_AbortToMark,	// abort asynchronous commands to mark
	kNkMAIDCommand_Abort,			// abort current asynchronous command
	kNkMAIDCommand_EnumChildren,	// requests add events for all child IDs
	kNkMAIDCommand_GetParent,		// gets previously opened parent for object
	kNkMAIDCommand_ResetToDefault	// resets all capabilities to their default value
};

enum eNkMAIDCapability
{
	kNkMAIDCapability_AsyncRate = 1,	// milliseconds between idle async calls
	kNkMAIDCapability_ProgressProc,	// callback during lengthy operation
	kNkMAIDCapability_EventProc,		// callback when event occurs
	kNkMAIDCapability_DataProc,		// callback to deliver data
	kNkMAIDCapability_UIRequestProc,	// callback to show user interface

	kNkMAIDCapability_IsAlive,			// FALSE if object is removed or parent closed
	kNkMAIDCapability_Children,		// IDs of children objects
	kNkMAIDCapability_State,			// current state of the object
	kNkMAIDCapability_Name,				// a string representing the name of the object
	kNkMAIDCapability_Description,	// a string describing the object
	kNkMAIDCapability_Interface,		// a string describing the interface to a device
	kNkMAIDCapability_DataTypes,		// what data types are supported or available
	kNkMAIDCapability_DateTime,		// date associated with an object
	kNkMAIDCapability_StoredBytes,	// read only size of object as stored on device

	kNkMAIDCapability_Eject,			// ejects media from a device
	kNkMAIDCapability_Feed,				// feeds media into a device
	kNkMAIDCapability_MediaPresent = kNkMAIDCapability_Feed + 2,	// TRUE if item has physical media to acquire

	kNkMAIDCapability_Mode,				// mode of this object
	kNkMAIDCapability_Acquire,			// begins the acquisition of the object
	kNkMAIDCapability_ForceScan,		// If FALSE, unneccesary scans can be eliminated

	kNkMAIDCapability_Start,			// start offset (in seconds) of the object
	kNkMAIDCapability_Length,			// length (in seconds) of the object
	kNkMAIDCapability_SampleRate,		// sampling rate (in samples/sec) of the object
	kNkMAIDCapability_Stereo,			// mono or stereo
	kNkMAIDCapability_Samples,			// given current state, read only number of samples

	kNkMAIDCapability_Filter,			// selects the filter for the light source
	kNkMAIDCapability_Prescan,			// sets the focus automatically
	kNkMAIDCapability_ForcePrescan,	// If FALSE, unneccesary prescans can be eliminated
	kNkMAIDCapability_ForceAutoFocus,// If FALSE, unneccesary autofocus can be eliminated
	kNkMAIDCapability_AutoFocusPt,	// sets the position to focus upon
	kNkMAIDCapability_Focus,			// sets the focus
	kNkMAIDCapability_Coords,			// rectangle of object in device units
	kNkMAIDCapability_Resolution,		// resolution of object (in pixels/inch)
	kNkMAIDCapability_Preview,			// preview or final acquire
	kNkMAIDCapability_Negative,		// negative or positive original
	kNkMAIDCapability_ColorSpace,		// color space
	kNkMAIDCapability_Bits,				// bits per color
	kNkMAIDCapability_Planar,			// interleaved or planar data transfer
	kNkMAIDCapability_Lut,				// LUT(s) for object
	kNkMAIDCapability_Transparency,	// light path of the original
	kNkMAIDCapability_Threshold,		// threshold level for lineart images
	kNkMAIDCapability_Pixels,			// given current state, read only size of image
	kNkMAIDCapability_NegativeDefault,// Default value for Negative capbility
	kNkMAIDCapability_Firmware,		// Firmware version

	kNkMAIDCapability_CommunicationLevel1,		// Device communication method (level 1)
	kNkMAIDCapability_CommunicationLevel2,		// Device communication method (level 2)
	kNkMAIDCapability_BatteryLevel,				// Device battery level
	kNkMAIDCapability_FreeBytes,					// Free bytes in device storage
	kNkMAIDCapability_FreeItems,					// Free items in device storage
	kNkMAIDCapability_Remove,						// Remove an object from device storage
	kNkMAIDCapability_FlashMode,					// Device flash (speedlight) mode
	kNkMAIDCapability_ModuleType,					// Module type
	kNkMAIDCapability_AcquireStreamStart,		// Starts a stream acquire
	kNkMAIDCapability_AcquireStreamStop,		// Stops a stream acquire
	kNkMAIDCapability_AcceptDiskAcquisition,	// Sets parameters for disk acquisition
	kNkMAIDCapability_Version,						// MAID version
	kNkMAIDCapability_FilmFormat,					// File Size (35mm, 6*6 etc...)
	kNkMAIDCapability_TotalBytes,					// Number of bytes in device storage
	kNkMAIDCapability_AutoFocus,					//Auto Focus
	kNkMAIDCapability_VendorBase = 0x8000	// vendor supplied capabilities start here
};

// The module will use one or more of these values in the kNkMAIDCapability_ColorSpace capability.
enum eNkMAIDColorSpace
{
	kNkMAIDColorSpace_LineArt,
	kNkMAIDColorSpace_Grey,
	kNkMAIDColorSpace_RGB,
	kNkMAIDColorSpace_sRGB,
	kNkMAIDColorSpace_CMYK,
	kNkMAIDColorSpace_Lab,
	kNkMAIDColorSpace_LCH,
	kNkMAIDColorSpace_AppleRGB,
	kNkMAIDColorSpace_ColorMatchRGB,
	kNkMAIDColorSpace_NTSCRGB,
	kNkMAIDColorSpace_BruceRGB,
	kNkMAIDColorSpace_AdobeRGB,
	kNkMAIDColorSpace_CIERGB,
	kNkMAIDColorSpace_AdobeWideRGB,
	kNkMAIDColorSpace_AppleRGB_Compensated,

	kNkMAIDColorSpace_VendorBase = 0x8000		// vendor supplied colorspaces start here
};

// The client will use these values with the kNkMAIDCapability_NegativeDefault capability.
enum eNkMAIDBooleanDefault
{
	kNkMAIDBooleanDefault_None,
	kNkMAIDBooleanDefault_True,
	kNkMAIDBooleanDefault_False
};

// The module will return one of more of these values in the kNkCapability_ModuleType capability.
enum eNkMAIDModuleTypes
{
	kNkMAIDModuleType_Scanner = 0x0001,
	kNkMAIDModuleType_Camera = 0x0002
};

// The module will use these values in the NkMAIDFileInfo structure when sending file data
// to the client in response to the kNkMAIDCapability_AcquireFile capability.
enum eNkMAIDFileDataTypes
{
	kNkMAIDFileDataType_NotSpecified,
	kNkMAIDFileDataType_JPEG,
	kNkMAIDFileDataType_TIFF,
	kNkMAIDFileDataType_FlashPix,
	kNkMAIDFileDataType_NIF,
	kNkMAIDFileDataType_QuickTime,
	kNkMAIDFileDataType_HEIF,
	kNkMAIDFileDataType_UserType = 0x100
};

// The module will use one or more of these values in the kNkMAIDCapability_FlashMode capability.
enum eNkMAIDFlashMode
{
	kNkMAIDFlashMode_FrontCurtain,
	kNkMAIDFlashMode_RearCurtain,
	kNkMAIDFlashMode_SlowSync,
	kNkMAIDFlashMode_RedEyeReduction,
	kNkMAIDFlashMode_SlowSyncRedEyeReduction,
	kNkMAIDFlashMode_SlowSyncRearCurtain
};

enum eNkMAIDFmmManualSetting
{
	kNkMAIDFmmManualSetting_NoSettting = 0,
	kNkMAIDFmmManualSetting_6mm,
	kNkMAIDFmmManualSetting_8mm,
	kNkMAIDFmmManualSetting_13mm,
	kNkMAIDFmmManualSetting_15mm,
	kNkMAIDFmmManualSetting_16mm,
	kNkMAIDFmmManualSetting_18mm,
	kNkMAIDFmmManualSetting_20mm,
	kNkMAIDFmmManualSetting_24mm,
	kNkMAIDFmmManualSetting_25mm,
	kNkMAIDFmmManualSetting_28mm,
	kNkMAIDFmmManualSetting_35mm,
	kNkMAIDFmmManualSetting_43mm,
	kNkMAIDFmmManualSetting_45mm,
	kNkMAIDFmmManualSetting_50mm,
	kNkMAIDFmmManualSetting_55mm,
	kNkMAIDFmmManualSetting_58mm,
	kNkMAIDFmmManualSetting_70mm,
	kNkMAIDFmmManualSetting_80mm,
	kNkMAIDFmmManualSetting_85mm,
	kNkMAIDFmmManualSetting_86mm,
	kNkMAIDFmmManualSetting_100mm,
	kNkMAIDFmmManualSetting_105mm,
	kNkMAIDFmmManualSetting_135mm,
	kNkMAIDFmmManualSetting_180mm,
	kNkMAIDFmmManualSetting_200mm,
	kNkMAIDFmmManualSetting_300mm,
	kNkMAIDFmmManualSetting_360mm,
	kNkMAIDFmmManualSetting_400mm,
	kNkMAIDFmmManualSetting_500mm,
	kNkMAIDFmmManualSetting_600mm,
	kNkMAIDFmmManualSetting_800mm,
	kNkMAIDFmmManualSetting_1000mm,
	kNkMAIDFmmManualSetting_1200mm,
	kNkMAIDFmmManualSetting_1400mm,
	kNkMAIDFmmManualSetting_1600mm,
	kNkMAIDFmmManualSetting_2000mm,
	kNkMAIDFmmManualSetting_2400mm,
	kNkMAIDFmmManualSetting_2800mm,
	kNkMAIDFmmManualSetting_3200mm,
	kNkMAIDFmmManualSetting_4000mm
};

enum eNkMAIDF0ManualSetting
{
	kNkMAIDF0ManualSetting_NoSettting = 0,
	kNkMAIDF0ManualSetting_F1_2,
	kNkMAIDF0ManualSetting_F1_4,
	kNkMAIDF0ManualSetting_F1_8,
	kNkMAIDF0ManualSetting_F2_0,
	kNkMAIDF0ManualSetting_F2_5,
	kNkMAIDF0ManualSetting_F2_8,
	kNkMAIDF0ManualSetting_F3_3,
	kNkMAIDF0ManualSetting_F3_5,
	kNkMAIDF0ManualSetting_F4_0,
	kNkMAIDF0ManualSetting_F4_5,
	kNkMAIDF0ManualSetting_F5_0,
	kNkMAIDF0ManualSetting_F5_6,
	kNkMAIDF0ManualSetting_F6_3,
	kNkMAIDF0ManualSetting_F7_1,
	kNkMAIDF0ManualSetting_F8_0,
	kNkMAIDF0ManualSetting_F9_5,
	kNkMAIDF0ManualSetting_F11,
	kNkMAIDF0ManualSetting_F13,
	kNkMAIDF0ManualSetting_F15,
	kNkMAIDF0ManualSetting_F16,
	kNkMAIDF0ManualSetting_F19,
	kNkMAIDF0ManualSetting_F22
};


#ifdef _WIN32
#pragma pack(pop)
#endif

#endif // (of #ifndef _MAID3_)

//================================================================================================
