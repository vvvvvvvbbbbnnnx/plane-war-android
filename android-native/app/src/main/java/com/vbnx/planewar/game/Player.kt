package com.vbnx.planewar.game

import android.graphics.Canvas
import android.graphics.Color
import android.graphics.Paint
import android.graphics.Path
import kotlin.random.Random

/** 玩家战机：跟随手指移动，自动开火 */
class Player(var x: Float = 0f, var y: Float = 0f) {

    val radius = 34f
    var alive = true

    /** 受击后的无敌时间（防止瞬间被秒） */
    var invincibleUntil: Long = 0L

    private val bodyPath = Path()

    val isInvincible: Boolean
        get() = System.currentTimeMillis() < invincibleUntil

    fun draw(canvas: Canvas, paint: Paint) {
        if (!alive) return

        // 无敌时闪烁
        if (isInvincible && (System.currentTimeMillis() / 90) % 2L == 0L) return

        val r = radius
        bodyPath.reset()
        bodyPath.moveTo(x, y - r * 1.4f)           // 机头
        bodyPath.lineTo(x + r * 0.28f, y - r * 0.2f)
        bodyPath.lineTo(x + r, y + r * 0.7f)       // 右机翼
        bodyPath.lineTo(x + r * 0.3f, y + r * 0.55f)
        bodyPath.lineTo(x + r * 0.22f, y + r)      // 右尾翼
        bodyPath.lineTo(x, y + r * 0.75f)
        bodyPath.lineTo(x - r * 0.22f, y + r)      // 左尾翼
        bodyPath.lineTo(x - r * 0.3f, y + r * 0.55f)
        bodyPath.lineTo(x - r, y + r * 0.7f)       // 左机翼
        bodyPath.lineTo(x - r * 0.28f, y - r * 0.2f)
        bodyPath.close()

        paint.style = Paint.Style.FILL
        paint.color = Color.parseColor("#4FC3F7")
        canvas.drawPath(bodyPath, paint)

        // 座舱
        paint.color = Color.parseColor("#E1F5FE")
        canvas.drawCircle(x, y - r * 0.3f, r * 0.16f, paint)

        // 尾焰（随机抖动）
        val flame = r * (0.45f + Random.nextFloat() * 0.35f)
        paint.color = Color.parseColor("#FFCA28")
        val flamePath = Path()
        flamePath.moveTo(x - r * 0.14f, y + r * 0.9f)
        flamePath.lineTo(x + r * 0.14f, y + r * 0.9f)
        flamePath.lineTo(x, y + r * 0.9f + flame)
        flamePath.close()
        canvas.drawPath(flamePath, paint)
    }
}
