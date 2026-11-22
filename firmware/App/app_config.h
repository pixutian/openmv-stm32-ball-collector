/*
 * app_config.h
 * -----------------------------------------------------------------------------
 * 整车可调参数集中在这里：底盘传动、速度档位、速度环、PWM 时序、电池估算。
 * 现场标定只需要改本文件，驱动层不用动。
 */

#ifndef APP_CONFIG_H
#define APP_CONFIG_H

/* ------------------------------ 底盘传动 ------------------------------ */
#define MOTOR_GEAR_RATIO          30      /* 减速箱速比 */
#define ENCODER_PULSE_PER_REV     13      /* 编码器线数：霍尔 13 线，GMR 500 线 */
#define ENCODER_EDGE_MULT         4       /* AB 两相四倍频计数 */
#define CONTROL_RATE_HZ           200     /* 速度环频率，与 TIM7 的 5ms 周期一致 */
/* 电机轴转速 = 计数 / (速比 * 线数 * 倍频) * 频率 * 60 */

/* ------------------------------ 速度档位 ------------------------------ */
/*
 * 共 7 档（0~6），第 3 档为中间档，也就是上电默认车速、越界回落的车速。
 * 每档目标转速 = GEAR_BASE_RPM + (档位 - GEAR_CENTER) * GEAR_STEP_RPM
 * 默认值：100 / 200 / 300 / 400 / 500 / 600 / 700
 */

/* ★★★ 小车初始速度就在这里改：改 GEAR_BASE_RPM 一个数即可 ★★★
 * GEAR_BASE_RPM 是上电默认车速，也是 7 档循环里的中间档（第 3 档）目标转速，
 * 单位是电机轴 rpm。想整车跑快就把这个数调大，想慢就调小；
 * 它同时也是"升到顶再按一下、降到 0 再按一下"回落到的那个速度。 */
#define GEAR_BASE_RPM             400     /* ← 初始车速（中间档目标转速，rpm） */

/* 档距：相邻两档的转速差，决定每按一次升/降档速度变化多少 */
#define GEAR_STEP_RPM             100     /* ← 每档差 100rpm */

/* 档位总数与中间档序号：GEAR_COUNT 固定 7，GEAR_CENTER 固定 3，一般不要改 */
#define GEAR_COUNT                7
#define GEAR_CENTER               3

/* ------------------------------ 转向与舵机 ---------------------------- */
#define TURN_RATE_SCALE           1.5f    /* 转向时目标转速的放大倍数 */
#define SERVO_NEUTRAL_DEG         90.0f   /* 舵机中位角 */
#define SERVO_TRAVEL_DEG          180.0f  /* 180° 舵机填 180，270° 舵机填 270 */

/* ------------------------------ 速度环 PI ----------------------------- */
#define SPEED_PI_KP               5.0f
#define SPEED_PI_KI               1.6f
#define PWM_OUTPUT_LIMIT          16700   /* PI 输出限幅，比 ARR 略小，给死区留余量 */

/* ------------------------------ PWM 时序 ------------------------------ */
#define MOTOR_PWM_ARR             16799   /* 电机 PWM 满量程，对应 100% 占空比 */
#define MOTOR_PWM_PSC             0       /* 168MHz 不分频，约 10kHz */
#define SERVO_PWM_ARR             19999   /* 舵机 50Hz */
#define SERVO_PWM_PSC             83

/* ------------------------------ 电池估算 ------------------------------ */
#define BAT_SAMPLE_CHANNEL        8       /* 电池采样通道，PB0 */
#define BAT_ADC_FULL_SCALE        4095.0f
#define BAT_ADC_REF_VOLT          3.3f
#define BAT_DIVIDER_RATIO         11.0f   /* 分压电阻比 */
#define BAT_VOLT_EMPTY            9.5f    /* 电量 0% 对应电压 */
#define BAT_VOLT_FULL             12.4f   /* 电量 100% 对应电压 */

/* ------------------------------ 叶片电机 7 档调速 ----------------------
 * 和底盘一样是 7 档循环，每档差 5% 占空比：
 *   第 0 档 70% / 1 档 75% / 2 档 80% / 3 档 85% / 4 档 90% / 5 档 95% / 6 档 100%
 * 第 3 档（85%）是中间档，调到顶或调到 0 后再按一次就回到这一档。
 *
 * 注意：占空比物理上限就是 100%，所以 100% 只能落在最高档；
 *       上电默认停在第 6 档（100%），保持满速上电行为。
 *       想上电就用中间档 85%，把 AUX_GEAR_BOOT 改成 3。
 *       若想保留 40%~100% 全范围，把 AUX_GEAR_COUNT 改为 13、AUX_GEAR_CENTER 改为 6。
 */
#define AUX_GEAR_COUNT            7       /* 档位总数 */
#define AUX_GEAR_CENTER           3       /* 中间档序号，越界回落目标 */
#define AUX_GEAR_STEP             5       /* ← 每档间距：5% 占空比 */
#define AUX_GEAR_TOP_DUTY         100     /* 最高档占空比（%） */
#define AUX_GEAR_BOOT             6       /* ← 上电所在档位，6 = 100% 满速 */

/* 上电瞬间的占空比：取最高档，等同于 AUX_GEAR_BOOT 对应值，保持一致 */
#define AUX_MOTOR_DEFAULT_DUTY    AUX_GEAR_TOP_DUTY

/* ------------------------------ 电气接口 ------------------------------ */
#define SERVO_ANGLE_REF_VOLT      500     /* 舵机 0° 对应比较值 */
#define SERVO_ANGLE_SPAN          2000    /* 全行程对应的比较值跨度 */

/* ------------------------------ 通讯参数 ------------------------------ */
#define DBG_UART_BAUD             115200  /* 调试串口 */
#define LINK_UART_BAUD            9600    /* 蓝牙模块出厂波特率 */
#define GEAR_KEY_DEBOUNCE_MS      200     /* 档位键去抖窗口，两次按键需间隔超过该值 */


/* ====================== 视觉自动收集参数（C30D 侧） ======================
 * 调参位置：本文件；改完需重新编译烧录 C30D。
 * OpenMV 端的识别参数不在这里，见 openmv/main_circle_pos.py 顶部。
 *
 * 通信：OpenMV P4/P5（UART3）<-> C30D PC11/PC10（UART4），115200 8N1
 * 帧：AA 55 TYPE LEN PAYLOAD CRC8
 * ====================================================================== */

/* 串口波特率：必须与 OpenMV 的 UART_BAUD 一致，改一边就要改另一边 */
#define VISION_BAUD              115200

/* 安全超时：超过该时间没收到有效目标帧 -> 四轮目标清零
 * 太小：球短暂丢失就停车；太大：丢球后还会往前冲。建议 300~500ms */
#define VISION_TIMEOUT_MS        300

/* 画面中心（按 QVGA 320x240；OpenMV 用 QQVGA 上报时已 ×2 换算成这个口径）
 * 如果改了 OpenMV 分辨率，这里要跟着改：QVGA=160，QQVGA=80（再确认换算） */
#define VISION_CENTER_PX         160.0f

/* 中心带宽：画面宽度的 1/5（320 -> ±32px）
 * dx 落在 ±BAND 内就“直接前进”，超出就原地转向
 * 想更容易进入前进状态：把分母改大（如 4.0 -> ±40px） */
#define VISION_BAND_PX           (VISION_CENTER_PX / 5.0f)

/* ★ 转向幅度（这次改小的参数）★
 * 带宽外原地转向速度 = 当前视觉速度 × VISION_TURN_RATE
 * 0.20 很柔和；0.30 默认；0.40~0.50 转向明显、容易左右摆
 * 改小 -> 转得慢、更稳；改大 -> 转得快、但容易过冲 */
#define VISION_TURN_RATE         0.30f

/* 视觉速度：默认 200 r/min；识别到球后按 RAMP 梯度升到 300 r/min
 * BASE：没加速前的目标速度；TRACK：追球时的目标速度
 * RAMP：每秒增加多少 rpm（100 -> 200 到 300 约 1 秒；改大更快） */
#define VISION_SPEED_BASE        200.0f
#define VISION_SPEED_TRACK       300.0f
#define VISION_SPEED_RAMP        100.0f

/* ★ 丢球续行（最后一刻看不到球时保证收球）★
 * 相机丢失目标后，按最后一次左右轮目标继续行进的时间（毫秒）
 * 1000 = 继续 1 秒；0 = 立即停车；太大可能冲过头
 * 只在“之前确实追过球”时生效，不会一直往前跑 */
#define VISION_LOST_HOLD_MS      200

/* ★ 无球搜索 ★
 * 长时间看不到球时：原地慢速旋转，每次约 60°，转完停 3s，共 6 次（约 360°）
 * 转完仍没球 -> 原地休息（不运动），直到再次识别到球
 * 搜索途中识别到球 -> 立即退出搜索，正常收集 */
#define VISION_SEARCH_AFTER_MS   5000     /* 无球多久开始搜索（ms） */
#define VISION_SEARCH_SPEED      120.0f   /* 原地旋转速度（r/min），慢速 */
#define VISION_SEARCH_60_MS      333    /* 转 60° 所需时间（ms），按实车标定 */
#define VISION_SEARCH_PAUSE_MS   3000     /* 每转 60° 后停 3s */
#define VISION_SEARCH_STEPS      6        /* 6 × 60° ≈ 360° */

/* 太近判定：目标面积超过 STOP_AREA 就后退，避免顶住球
 * 面积由 OpenMV 按 QVGA 等效值上报（πr²×4）；球越近值越大
 * 如果车总是顶到球：把 STOP_AREA 改小；如果不够近就后退：改大 */
#define VISION_STOP_AREA         4000
#define VISION_BACKOFF_RATIO     0.4f    /* 后退速度 = 当前视觉速度 × 该比例 */

/* 多球选择：C30D 按“最像球”评分选一个
 * score = W_CONF×conf + W_ROUND×round + W_AREA×面积归一化×100 + W_CENTER×居中×100
 * 想更信圆度：调大 W_ROUND；想优先近球：调大 W_AREA；想优先居中：调大 W_CENTER
 * 三个权重之和建议保持 1.0 左右 */
/* conf = OpenMV 给的“颜色相似度”（白/黄，0~100）
 * round = OpenMV 给的“形状相似度”（边缘清晰度，0~100） */
#define VISION_MAX_TARGETS       4
#define VISION_W_CONF            0.45f
#define VISION_W_ROUND           0.30f
#define VISION_W_AREA            0.15f
#define VISION_W_CENTER          0.10f

#endif /* APP_CONFIG_H */
