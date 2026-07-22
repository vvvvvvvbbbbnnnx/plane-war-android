package com.vbnx.planewar.game

import android.graphics.Canvas
import android.graphics.Color
import android.graphics.Paint
import android.graphics.Path

/** 敌机类型：小型快而脆，大型慢而硬且会反击 */
enum class EnemyType(
    val hp: Int,
    val speed: Float,   // px / 秒
    val score: Int,
    val radius: Float,
    val color: String
) {
    SMALL(1, 320f, 10, 26f, "#EF5350"),
    MEDIUM(3, 190f, 30, 38f, "#AB47BC"),
    LARGE(6, 110f, 60, 54f, "#FFA726")
}

class Enemy(
    val type: EnemyType,
    var x: Float,
    var y: Float,
    private val screenWidth: Float
) {
    var hp: Int = type.hp
    val radius: Float = type.radius
    private var driftPhase = (0..628).random() / 100f
    private var fireCooldown = 1.2f + (0..150).random() / 100f

    /** 大敌机缓慢左右漂移 */
    fun update(dt: Float) {
        y += type.speed * dt
        driftPhase += dt * 2f
        if (type != EnemyType.SMALL) {
            x += kotlin.math.sin(driftPhase) * 60f * dt
            x = x.coerceIn(radius, screenWidth - radius)
        }
    }

    /** 大型敌机定期反击，返回是否该开火 */
    fun shouldFire(dt: Float, screenHeight: Float): Boolean {
        if (type != EnemyType.LARGE || y < 0 || y > screenHeight * 0.6f) return false
        fireCooldown -= dt
        if (fireCooldown <= 0f) {
            fireCooldown = 1.8f + (0..100).random() / 100f
            return true
        }
        return false
    }

    fun isOffScreen(screenHeight: Float): Boolean = y - radius > screenHeight

    fun draw(canvas: Canvas, paint: Paint) {
        val r = radius
        paint.style = Paint.Style.FILL
        paint.color = Color.parseColor(type.color)

        val path = Path()
        // 敌机机头朝下
        path.moveTo(x, y + r * 1.2f)
        path.lineTo(x + r * 0.3f, y + r * 0.1f)
        path.lineTo(x + r, y - r * 0.6f)
        path.lineTo(x + r * 0.3f, y - r * 0.45f)
        path.lineTo(x + r * 0.2f, y - r)
        path.lineTo(x, y - r * 0.7f)
        path.lineTo(x - r * 0.2f, y - r)
        path.lineTo(x - r * 0.3f, y - r * 0.45f)
        path.lineTo(x - r, y - r * 0.6f)
        path.lineTo(x - r * 0.3f, y + r * 0.1f)
        path.close()
        canvas.drawPath(path, paint)

        // 座舱
        paint.color = Color.parseColor("#212121")
        canvas.drawCircle(x, y + r * 0.2f, r * 0.15f, paint)

        // 血条（多血敌机）
        if (type.hp > 1) {
            val barW = r * 1.6f
            val barH = 6f
            val left = x - barW / 2
            val top = y - r * 1.35f
            paint.color = Color.parseColor("#616161")
            canvas.drawRect(left, top, left + barW, top + barH, paint)
            paint.color = Color.parseColor("#76FF03")
            canvas.drawRect(left, top, left + barW * hp / type.hp, top + barH, paint)
        }
    }
}
